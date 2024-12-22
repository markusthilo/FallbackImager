/* zd */
/* Written for POSIX + gcc */
/* Author: Markus Thilo */
/* E-mail: markus.thilo@gmail.com */
/* License: GPL-3 */

/* Version */
const char *VERSION = "1.0.1_2024-12-22";

#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <time.h>
#include <sys/stat.h>

/* Parameters to the target (file or device) */
typedef struct target_t {
	char *path;	// string with path to device or file
    FILE *file;	// file handler
	size_t size;	// the full size to work
	size_t ptr; // pointer to position in file
	int64_t blocks;	// number of full blocks
	int64_t leftbytes;	// number of bytes afte last full block
} target_t;

/* Options for the wiping process */
typedef struct config_t {
	int64_t bs;	// size of blocks in bytes
	int64_t bs64;	// size of blocks in 64 bit chunks (=bs/8)
	uint8_t value;	// value to write and/or verify
	uint64_t value64;	// value expanded to 64 bits = 8 bytes
	uint8_t *block;	// block to write
} config_t;

/* To handle bad blocks */
typedef struct badblocks_t {
	int cnt;	// counter for bad blocks
	int max;	// abort after
	int retry;	// limit retries
	int64_t *offsets;	// offsets
	char *errors;	// type of error
} badblocks_t;

time_t glob_time;	// global variable to messure time zd ran

/* Print help text */
void help(const int r) {
	printf("\n              000\n");
	printf("              000\n");
	printf("              000\n");
	printf("00000000  0000000\n");
	printf("   0000  0000 000\n");
	printf("  0000   000  000\n");
	printf(" 0000    0000 000\n");
	printf("00000000  0000000\n\n");
	printf("v%s\n\n", VERSION);
	printf("Wipe block device, partition, file etc.\n\n");
	printf("Usage:\n");
	printf("zd [OPTIONS] TARGET \n");
	printf("(or zd -h for this help)\n\n");
	printf("TARGET:\n");
	printf("    Block device/partition/file/...\n\n");
	printf("OPTIONS (optional):\n");
	printf("    -a : overwrite all bytes, do not check if already wiped\n");
	printf("    -b BLOCK_SIZE : block size for read and write (default is 4096)\n");
	printf("    -f VALUE : write this byte given in hex instead of 0\n");
	printf("    -m MAX_BAD_BLOCKS : abort after bad blocks (default is 200)\n");
	printf("    -r MAX_RETRIES : maximum retries after read or write error (default is 200)\n");
	printf("    -v : verify, do not wipe\n");
	printf("    -x : Two pass wipe (1st pass writes random bytes)\n\n");
	printf("Bad blocks will be listed as offset/[rwu]:\n");
	printf("    r: error occured while reading\n");
	printf("    w: error occured while writing\n");
	printf("    u: block is not wiped (unwiped)\n\n");
	printf("Example:\n");
	printf("zd /dev/sdc\n\n");
	printf("Disclaimer:\n");
	printf("The author is not responsible for any loss of data.\n");
	printf("Obviously, this tool is dangerous as it is designed to erase data.\n\n");
	printf("Author: Markus Thilo\n");
	printf("License: GPL-3\n");
	printf("This CLI tool is part of the FallbackImager project:\n");
	printf("https://github.com/markusthilo/FallbackImager\n\n");
	exit(r);
}

/* Print time delta in hours, minutes and seconds */
void print_hms(const time_t start_time) {
	int delta = time(NULL) - start_time;
	int hours = delta / 3600;
	delta -= hours * 3600;
	int minutes = delta / 60;
	delta -= minutes * 60;
	if ( hours == 1 ) printf("1 hour, ");
	else if ( hours > 1 ) printf("%d hours, ", hours);
	if ( minutes == 1 ) printf("1 minute, ");
	else if ( minutes > 1 ) printf("%d minutes, ", minutes);
	if ( delta == 1 ) printf("1 second\n");
	else printf ("%d seconds\n", delta);
}

/* Print time running the app took and exit by given returncode */
void sysexit(const int r) {
	printf("\n\nThe application ran ");
	print_hms(glob_time);
	printf("\n");
	exit(r);
}

/* Print time a process took */
void print_time(const time_t start_time) {
	printf("\n\nProcess took ");
	print_hms(start_time);
}

/* Open file/device */
void open_target(target_t *target, char *mode) {
	target->file = fopen(target->path, mode);
	if ( target->file == NULL ) {
		fprintf(stderr, "Error: could not open %s\n", target->path);
		sysexit(1);
	}
	target->ptr = 0;
}

/* Set file pointer to given offset */
void set_pointer(target_t *target, const size_t offset) {
	const size_t position = target->ptr + offset;
	if ( fseek(target->file, position, SEEK_SET) != 0 ) {
		fprintf(stderr, "Error: could not point to position %ld in %s\n", position, target->path);
		fclose(target->file);
		sysexit(1);
	}
}

/* Move file pointer by given offset*/
void move_pointer(target_t *target, const size_t offset) {
	if ( fseek(target->file, offset, SEEK_CUR) != 0 ) {
		fprintf(stderr, "Error: could not move pointer to position %ld in %s\n", target->ptr + offset, target->path);
		fclose(target->file);
		sysexit(1);
	}
}

/* Set file pointer to 0 = beginning */
void reset_pointer(target_t *target) {
	rewind(target->file);
	target->ptr = 0;
}

/* Check if block is wiped */
int check_block(const uint64_t *block, const config_t *conf){
	for (int i=0; i<conf->bs64; i++) if ( block[i] != conf->value64 ) return -1;
	return 0;
}

/* Check if given quantity of bytes is wiped */
int check_bytes(const uint8_t *block, const config_t *conf, const size_t bs){
	for (int i=0; i<bs; i++) if ( block[i] != conf->value ) return -1;
	return 0;
}

/* Print bad blocks */
void print_bad_blocks(const badblocks_t *badblocks) {
	printf("Found %d bad block(s) (OFFSET/ERROR -> r = read error, w = write error, u = unwiped block):",
		badblocks->cnt);
	for (int i=0; i<badblocks->cnt; i++) {
			if ( i % 4 == 0 ) printf("\n");
			else printf("  ");
		printf("%*ld/%c", 20, badblocks->offsets[i], badblocks->errors[i]);
	}
	printf("\n");
}

/* Check for too many bad blocks */
void check_max_bad_blocks(const target_t *target, badblocks_t *badblocks) {
	if ( badblocks->max > badblocks->cnt++ ) return;
	fclose(target->file);
	printf("\n\n");
	print_bad_blocks(badblocks);
	fprintf(stderr, "Error: aborting because of too many bad blocks\n");
	sysexit(1);
}

/* Handle unwiped block */
void wipe_error(const target_t *target, badblocks_t *badblocks, const size_t bs) {
	badblocks->offsets[badblocks->cnt] = target->ptr;
	badblocks->errors[badblocks->cnt] = 'u';
	check_max_bad_blocks(target, badblocks);
}

/* Handle read error */
int read_error(target_t *target, const config_t *conf, badblocks_t *badblocks, const size_t bs) {
	fprintf(stderr, "\nError: read error at offset %ld\n", target->ptr);
	uint8_t *block = malloc(bs);
	for (int pass=0; pass<badblocks->retry; pass++) {	// loop retries
		set_pointer(target, 0);
		if ( fread(block, bs, 1, target->file) == 1 ) return 0;
	}
	badblocks->offsets[badblocks->cnt] = target->ptr;	// add this bad block
	badblocks->errors[badblocks->cnt] = 'r';	// mark as read error
	check_max_bad_blocks(target, badblocks);
	set_pointer(target, bs);	// point to next block
	return -1;
}

/* Handle write error */
void write_error(target_t *target, const config_t *conf, badblocks_t *badblocks, const size_t bs) {
	fprintf(stderr, "\nError: write error at offset %ld\n", target->ptr);
	uint8_t *block = malloc(bs);
	for (int pass=0; pass<badblocks->retry; pass++) {	// loop retries
		set_pointer(target, 0);
		if ( fwrite(conf->block, bs, 1, target->file) == 1 ) return;
	}
	badblocks->offsets[badblocks->cnt] = target->ptr;	// add this bad block
	badblocks->errors[badblocks->cnt] = 'w';	// mark as read error
	check_max_bad_blocks(target, badblocks);
	set_pointer(target, bs);	// go to next block
}

/* Print progress */
clock_t print_progress(const target_t *target) {
	printf("\r...%*d%% / %*ld of%*ld bytes",
		4, (int)((100*target->ptr)/target->size), 20, target->ptr, 20, target->size);
	fflush(stdout);
	return time(NULL);
}

/* Wipe target, overwrite all */
void wipe_all(target_t *target, const config_t *conf, badblocks_t *badblocks) {
	if ( target->size >= conf->bs ) {
		clock_t now = print_progress(target);
		for (off_t bc=0; bc<target->blocks; bc++) {
			if ( fwrite(conf->block, conf->bs, 1, target->file) != 1 )
				write_error(target, conf, badblocks, conf->bs);
			if ( time(NULL) > now ) now = print_progress(target);
			target->ptr += conf->bs;
		}
	}
	if ( target->leftbytes > 0 )
		if ( fwrite(conf->block, target->leftbytes, 1, target->file) != 1 )
				write_error(target, conf, badblocks, target->leftbytes);
	target->ptr = target->size;
	print_progress(target);
}

/* Convert value of a command line argument to integer >= 0, return -1 if NULL */
int uint_arg(const char *value, const char arg) {
	if ( value == NULL ) return -1;
	int res = atoi(value);
	if ( res >= 1 ) return res;
	if ( strcmp(value, "0") == 0 ) return 0;
	fprintf(stderr, "Error: -%c needs an unsigned integer value\n", arg);
	sysexit(1);
}

/* Main function - program starts here */
int main(int argc, char **argv) {
	if ( ( argc > 1 )	// show help
	&& ( ( ( argv[1][0] == '-' ) && ( argv[1][1] == '-' ) && ( argv[1][2] == 'h' ) )
	|| ( ( argv[1][0] == '-' ) && ( argv[1][1] == 'h' ) ) ) ) help(0);
	else if ( argc < 2 ) help(1);	// also show help if no argument is given but return with exit(1)
	time(&glob_time);	// start messsuring time
	char opt;	// command line options
	target_t target;	// drive or file
	config_t conf;	// options for wipe process
	badblocks_t badblocks;	// to abort after n bad blocks
	time_t start_time;	// to measure time
	int todo = 0;	// 0 = selective wipe, 1 = all blocks, 2 = 2pass, 3 = verify
	char *barg = NULL, *farg = NULL, *marg = NULL, *rarg = NULL;	// pointer to command line args
	while ((opt = getopt(argc, argv, "avxb:f:m:r:")) != -1)	// command line arguments
		switch (opt) {
			case 'a': if ( todo == 0 ) { todo = 1; break; }
			case 'x': if ( todo == 0 ) { todo = 2; break; }
			case 'v': if ( todo == 0 ) { todo = 3; break; }
				fprintf(stderr, "Error: too many arguments\n");
				exit(1);
			case 'b': barg = optarg; break;	// get blocksize
	        case 'f': farg = optarg; break;	// get value to write and/or verify
			case 'm': marg = optarg; break;	// get value for max badb locks
			case 'r': rarg = optarg; break;	// get value for max retries
			case '?':
				switch (optopt) {
					case 'b': fprintf(stderr, "Error: option -b requires a value (blocksize)\n"); exit(1);
					case 'f': fprintf(stderr, "Error: option -f requires a value (hex integer)\n"); exit(1);
					default: help(1);
				}
			default: help(1);
		}
	if ( argc != optind+1 ) {	// check if there is one input file
		fprintf(stderr, "Error: one device or file to wipe is required\n");
		exit(1);
	}
	target.path = argv[optind];
	int bvalue = uint_arg(barg, 'b');
	if  ( bvalue == -1 ) conf.bs = 4096;	// default
	else if ( bvalue < 512 || bvalue > 32768 || bvalue % 512 != 0 ) {
		fprintf(stderr, "Error: block size has to be n * 512, >=512 and <=32768\n");
		exit(1);
	} else conf.bs = bvalue;
	conf.bs64 = conf.bs >> 3;	// number of 64 bit blocks = block size / 8
	conf.block = malloc(conf.bs);
	conf.value = 0;	//	default is to wipe with zeros
	conf.value64 = 0;
	if ( farg != NULL ) {
		unsigned long int fvalue = strtoul(farg, NULL, 16);
		if ( fvalue < 0 || fvalue > 0xff ) {	// check for 8 bits
			fprintf(stderr, "Error: value has to be inbetween 0 and 0xff\n");
			exit(1);
		}
		conf.value = (char) fvalue;
		memset(&conf.value64, conf.value, sizeof(conf.value64));
	}
	badblocks.max = uint_arg(marg, 'm');
	if ( badblocks.max == -1 ) badblocks.max = 200;	// default
	badblocks.retry = uint_arg(rarg, 'r');
	if ( badblocks.retry == -1 ) badblocks.retry = 200;	// default
	open_target(&target, "rb");	// determin size
	fseek(target.file, 0, SEEK_END);
	target.size = ftell(target.file);
	fclose(target.file);
	if ( target.size <= 0 ) {
		if ( target.size == 0 ) fprintf(stderr, "Error: size of target seems to be 0 or you have no access\n");
		else fprintf(stderr, "Error: could not determin size of target\n");
		exit(1);
	}
	target.blocks = target.size / conf.bs;	// full blocks
	target.leftbytes = target.size % conf.bs;
	badblocks.cnt = 0;
	badblocks.offsets = malloc(sizeof(size_t) * badblocks.max);
	badblocks.errors = malloc(sizeof(char) * badblocks.max);
	time(&start_time);
	switch (todo) {
		case 0:	// normal/selective wipe
			memset(conf.block, conf.value, conf.bs);
			size_t negbs = -1 * conf.bs;
			printf("Pass 1 of 2, wiping %s\n", target.path);
			open_target(&target, "rb+");
			if ( target.size >= conf.bs ) {
				uint64_t *block = malloc(conf.bs);
				clock_t now = print_progress(&target);
				for (size_t bc=0; bc<target.blocks; bc++) {
					if ( fread(block, conf.bs, 1, target.file) != conf.bs || check_block(block, &conf) == -1 ) {
						move_pointer(&target, negbs);	// overwrite block/page
						if ( fwrite(conf.block, conf.bs, 1, target.file) != 1 )
							write_error(&target, &conf, &badblocks, conf.bs);
					}
					if ( time(NULL) > now ) now = print_progress(&target);
					target.ptr += conf.bs;
				}
				if ( target.leftbytes > 0 ) {
					uint8_t *block = malloc(target.leftbytes);
					if ( fread(block, target.leftbytes, 1, target.file) != target.leftbytes
						|| check_bytes(block, &conf, target.leftbytes) == -1 ) {
							move_pointer(&target, negbs);	// overwrite block/page
							if ( fwrite(conf.block, target.leftbytes, 1, target.file) != 1)
								write_error(&target, &conf, &badblocks, target.leftbytes);
					}
				}
			}
			target.ptr = target.size;
			print_progress(&target);
			break;
		case 1:	// wipe all blocks
			memset(conf.block, conf.value, conf.bs);
			printf("Pass 1 of 2, wiping %s\n", target.path);
			open_target(&target, "wb");
			wipe_all(&target, &conf, &badblocks);
			break;
		case 2:	// 2pass wipe
			for (int i=0; i<conf.bs; i++) conf.block[i] = (uint8_t)rand();
			printf("Pass 1 of 3, wiping %s\n", target.path);
			open_target(&target, "wb");
			wipe_all(&target, &conf, &badblocks);
			print_time(start_time);
			if ( badblocks.cnt > 0 ) {
				printf("Warning: finished 1st pass but found bad blocks\n");
				print_bad_blocks(&badblocks);
			}
			printf("Running sync, this might take some minutes...\n");
			time(&start_time);
			sync();
			print_time(start_time);
			badblocks.cnt = 0;
			reset_pointer(&target);
			time(&start_time);
			memset(conf.block, conf.value, conf.bs);
			printf("Pass 2 of 3, wiping %s\n", target.path);
			wipe_all(&target, &conf, &badblocks);
			break;
		case 3:	// verify
			memset(conf.block, conf.value, conf.bs);
	}
	if ( todo == 3 ) printf("Verifying %s\n", target.path);
	else {
		print_time(start_time);
		if ( badblocks.cnt > 0 ) {
			printf("Warning: finished wiping but found bad blocks\n");
			print_bad_blocks(&badblocks);
		}
		printf("Running fclose and sync, this might take some minutes...\n");
		time(&start_time);
		fclose(target.file);
		sync();
		print_time(start_time);
		time(&start_time);
		if ( todo == 2 ) printf("Pass 3 of 3"); else printf("Pass 2 of 2");
		printf(", verifying %s\n", target.path);
	}
	badblocks.cnt = 0;	// verification pass
	open_target(&target, "rb");
	if ( target.size >= conf.bs ) {
		uint64_t *block = malloc(conf.bs);
		clock_t now = print_progress(&target);
		for (off_t bc=0; bc<target.blocks; bc++) {
			if ( fread(block, conf.bs, 1, target.file) != 1
				&& read_error(&target, &conf, &badblocks, conf.bs) == -1 ) {
				target.ptr += conf.bs;
				continue;
			}
			if ( check_block(block, &conf) == -1 ) wipe_error(&target, &badblocks, conf.bs);
			if ( time(NULL) > now ) now = print_progress(&target);
			target.ptr += conf.bs;
		}
	}
	if ( target.leftbytes > 0 ) {
		uint8_t *block = malloc(target.leftbytes);
		if ( fread(block, target.leftbytes, 1, target.file) != 1
			&& read_error(&target, &conf, &badblocks, target.leftbytes) == 0
			&& check_bytes(block, &conf, target.leftbytes) == -1
		) wipe_error(&target, &badblocks, target.leftbytes);
		target.ptr = target.size;
	}
	print_progress(&target);
	print_time(start_time);
	fclose(target.file);
	if ( badblocks.cnt > 0 ) {
		printf("Warning: all done but found bad blocks\n");
		print_bad_blocks(&badblocks);
		fprintf(stderr, "Error: %d bad blocks in %s\n", badblocks.cnt, target.path);
		sysexit(1);
	}
	printf("Verification was succesful, all done\n");
	sysexit(0);
}
