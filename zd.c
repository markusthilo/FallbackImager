/* zd */
/* Written for POSIX + gcc */
/* Author: Markus Thilo */
/* E-mail: markus.thilo@gmail.com */
/* License: GPL-3 */

/* Version */
const char *VERSION = "0.0.1_2023-12-04";

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
    int file;	// file descriptor
	off_t size;	// the full size to work
	off_t ptr; // pointer to position in file
	off_t blocks;	// number of full blocks
	size_t leftbytes;	// number of bytes afte last full block
} target_t;

/* Options for the wiping process */
typedef struct config_t {
	size_t bs;	// size of blocks in bytes
	int bs64;	// size of blocks in 64 bit chunks (=bs/8)
	uint8_t value;	// value to write and/or verify
	uint64_t value64;	// value expanded to 64 bits = 8 bytes
	uint8_t *block;	// block to write
} config_t;

/* To handle bad blocks */
typedef struct badblocks_t {
	int cnt;	// counter for bad blocks
	int max;	// abort after
	int retry;	// limit retries
	off_t *offsets;	// offsets
	char *errors;	// type of error
} badblocks_t;

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
	printf("Wipe drive or file\n\n");
	printf("Usage:\n");
	printf("zd [OPTIONS] TARGET \n");
	printf("(or zd -h for this help)\n\n");
	printf("TARGET:\n");
	printf("    File or physical drive\n\n");
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
	printf("Obviously, the tool is dangerous as it is designed to erase data.\n\n");
	printf("Author: Markus Thilo\n");
	printf("License: GPL-3\n");
	printf("This CLI tool is part of the FallbackImager project:\n");
	printf("https://github.com/markusthilo/FallbackImager\n\n");
	exit(r);
}

/* Set file pointer */
void set_pointer(target_t *target, const off_t ptr) {
	if ( lseek(target->file, ptr, SEEK_SET) != ptr ) {
		fprintf(stderr, "Error: could not point to position %ld in %s\n",
			ptr, target->path);
		close(target->file);
		exit(1);
	}
	target->ptr = ptr;
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
void print_bad_blocks(badblocks_t *badblocks) {
		printf(" found %d bad block(s) (offset/[rwu]):\n", badblocks->cnt);
		for (int i=0; i<badblocks->cnt-1; i++)
			printf("%lu/%c, ", badblocks->offsets[i], badblocks->errors[i]);
		printf("%lu/%c\n\n", badblocks->offsets[badblocks->cnt-1], badblocks->errors[badblocks->cnt-1]);
}

/* Check for oo many bad blocks */
void check_max_bad_blocks(badblocks_t *badblocks) {
	if ( badblocks->max > badblocks->cnt++ ) return;
	printf("\nWarning:");
	print_bad_blocks(badblocks);
	fprintf(stderr, "\nError: tolerance exceeded\n");
	exit(1);
}

/* Handle unwiped block */
void wipe_error(const target_t *target, badblocks_t *badblocks, const size_t bs) {
	fprintf(stderr, "\nWarning: unwiped block at offset %ld\n", target->ptr);
	badblocks->offsets[badblocks->cnt] = target->ptr;
	badblocks->errors[badblocks->cnt] = 'u';
	check_max_bad_blocks(badblocks);
}

/* Handle read error */
void read_error(target_t *target, const config_t *conf, badblocks_t *badblocks, const size_t bs) {
	fprintf(stderr, "\nError: read error at offset %ld\n", target->ptr);
	uint8_t *block = malloc(bs);
	for (int pass=0; pass<badblocks->retry; pass++) {	// loop retries
		set_pointer(target, target->ptr);
		if ( read(target->file, block, bs) == bs ) {
			if ( check_bytes(block, conf, bs) == -1 ) check_max_bad_blocks(badblocks);
			target->ptr += bs;
			return;
		}
	}
	badblocks->offsets[badblocks->cnt] = target->ptr;	// add this bad block
	badblocks->errors[badblocks->cnt] = 'r';	// mark as read error
	set_pointer(target, target->ptr+bs);	// go to next block
	check_max_bad_blocks(badblocks);
}

/* Handle write error */
void write_error(target_t *target, const config_t *conf, badblocks_t *badblocks, const size_t bs) {
	fprintf(stderr, "\nError: write error at offset %ld\n", target->ptr);
	uint8_t *block = malloc(bs);
	for (int pass=0; pass<badblocks->retry; pass++) {	// loop retries
		set_pointer(target, target->ptr);
		if ( write(target->file, conf->block, bs) == bs ) {
			target->ptr += bs;
			return;
		}
	}
	badblocks->offsets[badblocks->cnt] = target->ptr;	// add this bad block
	badblocks->errors[badblocks->cnt] = 'w';	// mark as read error
	set_pointer(target, target->ptr+bs);	// go to next block
	check_max_bad_blocks(badblocks);
}

/* Print progress */
clock_t print_progress(const target_t *target) {
	const clock_t onesec = 1000000 / CLOCKS_PER_SEC;
	printf("\r...%*d%% / %*ld of%*ld bytes",
		4, (int)((100*target->ptr)/target->size), 20, target->ptr, 20, target->size);
	fflush(stdout);
	return clock() + onesec;
}

/* Wipe target, overwrite all */
void wipe_all(target_t *target, const config_t *conf, badblocks_t *badblocks) {
	if ( target->size >= conf->bs ) {
		clock_t next_second = print_progress(target);
		for (off_t bc=0; bc<target->blocks; bc++) {
			if ( write(target->file, conf->block, conf->bs ) != conf->bs )
				write_error(target, conf, badblocks, conf->bs);
			if ( clock() >= next_second ) next_second = print_progress(target);
			target->ptr += conf->bs;
		}
	}
	if ( target->leftbytes > 0 )
		if ( write(target->file, conf->block, target->leftbytes ) != target->leftbytes )
				write_error(target, conf, badblocks, target->leftbytes);
	target->ptr = target->size;
	print_progress(target);
}

/* Convert value of a command line argument to integer > 0, return -1 if NULL */
int uint_arg(const char *value, const char arg) {
	if ( value == NULL ) return -1;
	int res = atoi(value);
	if ( res >= 1 ) return res;
	if ( strcmp(value, "0") == 0 ) return 0;
	fprintf(stderr, "Error: -%c needs an unsigned integer value\n", arg);
	exit(1);
}

/* Print block to stdout */
void print_block(target_t *target, const off_t ptr) {
	set_pointer(target, ptr);
	off_t bs = target->size - target->ptr;
	if ( bs > 512 ) bs = 512;	// do not show more than 512 bytes
	uint8_t *block = malloc(bs);
	if ( read(target->file, block, bs) != bs ) {
		fprintf(stderr, "\nError: could not read block of %ld bytes at offset %ld\n",
			bs, target->ptr);
		close(target->file);
		exit(1);
	}
	printf("Bytes %ld - %ld", target->ptr, target->ptr + bs);
	target->ptr += bs;
	int t = 1;
	for (int i=0; i<bs; i++) {
		if ( --t == 0 ) {
			printf("\n");
			t = 32;
		}
		printf("%02X ", block[i]);
	}
	printf("\n");
}

/* Print time delta */
void print_time(const time_t start_time) {
	int delta = (clock() - start_time) / CLOCKS_PER_SEC;
	int h = delta/3600;
	int m = (delta - h*3600)/60;
	int s = delta - h*3600 - m*60;
	printf("\nProcess took %d hour(s), %d minute(s) and %d second(s)\n", h, m, s);
}

/* Main function - program starts here */
int main(int argc, char **argv) {
	if ( ( argc > 1 )	// show help
	&& ( ( ( argv[1][0] == '-' ) && ( argv[1][1] == '-' ) && ( argv[1][2] == 'h' ) )
	|| ( ( argv[1][0] == '-' ) && ( argv[1][1] == 'h' ) ) ) ) help(0);
	else if ( argc < 2 ) help(1);	// also show help if no argument is given but return with exit(1)
	char opt;	// command line options
	target_t target;	// drive or file
	config_t conf;	// options for wipe process
	badblocks_t badblocks;	// to abort after n bad blocks
	int todo = 0;	// 0 = selective wipe, 1 = all blocks, 2 = 2pass, 3 = verify
	time_t start_time;	// to measure
	char *barg = NULL, *farg = NULL, *marg = NULL, *rarg = NULL;	// pointer to command line args
	while ((opt = getopt(argc, argv, "avxb:f:m:")) != -1)	// command line arguments
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
		if ( fvalue < 1 || fvalue > 0xff ) {	// check for 8 bits
			fprintf(stderr, "Error: value has to be inbetween 1 and 0xff\n");
			exit(1);
		}
		conf.value = (char) fvalue;
		for (int shift=0; shift<=56; shift+=8) conf.value64 |= (fvalue << shift);	// expand to 64 bits
	}
	badblocks.max = uint_arg(marg, 'm');
	if ( badblocks.max == -1 ) badblocks.max = 200;	// default
	badblocks.retry = uint_arg(rarg, 'r');
	if ( badblocks.retry == -1 ) badblocks.retry = 200;	// default
	if ( todo == 3 ) target.file = open(target.path, O_RDONLY);	// open device/file
	else target.file = open(target.path, O_RDWR);
	if ( target.file < 0 ) {
		fprintf(stderr, "Error: could not open %s\n", target.path);
		exit(1);
	}
	target.size = lseek(target.file, 0, SEEK_END);
	if ( target.size <= 0 ) {
		if ( target.size == 0 ) fprintf(stderr, "Error: size of target seems to be 0\n");
		else fprintf(stderr, "Error: could not determin size of target\n");
		close(target.file);
		exit(1);
	}
	target.blocks = target.size / conf.bs;	// full blocks
	target.leftbytes = target.size % conf.bs;
	set_pointer(&target, 0);
	badblocks.cnt = 0;
	badblocks.offsets = malloc(sizeof(off_t) * badblocks.max);
	badblocks.errors = malloc(sizeof(char) * badblocks.max);
	start_time = clock();
	switch (todo) {
		case 0:	// normal/selective wipe
			memset(conf.block, conf.value, conf.bs);
			printf("Wiping\n");
			if ( target.size >= conf.bs ) {
				uint64_t *block = malloc(conf.bs);
				clock_t next_second = print_progress(&target);
				for (size_t bc=0; bc<target.blocks; bc++) {
					if ( read(target.file, block, conf.bs) != conf.bs ) {
						read_error(&target, &conf, &badblocks, conf.bs);
						continue;
					}
					if ( check_block(block, &conf) == -1 ) {	// overwrite block/page
						set_pointer(&target, target.ptr);
						if ( write(target.file, conf.block, conf.bs ) != conf.bs )
							write_error(&target, &conf, &badblocks, conf.bs);
					}
					if ( clock() >= next_second ) next_second = print_progress(&target);
					target.ptr += conf.bs;
				}
				if ( target.leftbytes > 0 ) {
					uint8_t *block = malloc(target.leftbytes);
					if ( read(target.file, block, target.leftbytes) != target.leftbytes )
						read_error(&target, &conf, &badblocks, target.leftbytes);
					else {
						if ( check_bytes(block, &conf, target.leftbytes) == -1 ) {
							set_pointer(&target, target.ptr);
							if ( write(target.file, conf.block, target.leftbytes ) != target.leftbytes )
								write_error(&target, &conf, &badblocks, target.leftbytes);
						}
					}
				}
			}
			break;
		case 1:	// wipe all blocks
			memset(conf.block, conf.value, conf.bs);
			printf("Wiping\n");
			wipe_all(&target, &conf, &badblocks);
			break;
		case 2:	// 2pass wipe
			for (int i=0; i<conf.bs; i++) conf.block[i] = (uint8_t)rand();
			printf("Wiping, pass 1 of 2\n");
			wipe_all(&target, &conf, &badblocks);
			print_time(start_time);
			start_time = clock();
			set_pointer(&target, 0);
			badblocks.cnt = 0;
			memset(conf.block, conf.value, conf.bs);
			printf("Wiping, pass 2 of 2\n");
			wipe_all(&target, &conf, &badblocks);
	}
	if ( todo != 3 ) {
		print_progress(&target);
		print_time(start_time);
		start_time = clock();
	}
	printf("Verifying\n");	// verification pass
	if ( target.ptr != 0 ) set_pointer(&target, 0);
	badblocks.cnt = 0;
	if ( target.size >= conf.bs ) {
		uint64_t *block = malloc(conf.bs);
		clock_t next_second = print_progress(&target);
		for (off_t bc=0; bc<target.blocks; bc++) {
			if ( read(target.file, block, conf.bs) != conf.bs ) {
				read_error(&target, &conf, &badblocks, conf.bs);
				continue;
			}
			if ( check_block(block, &conf) == -1 ) wipe_error(&target, &badblocks, conf.bs);
			if ( clock() >= next_second ) next_second = print_progress(&target);
			target.ptr += conf.bs;
		}
	}
	if ( target.leftbytes > 0 ) {
		uint8_t *block = malloc(target.leftbytes);
		if ( read(target.file, block, target.leftbytes) != target.leftbytes )
			read_error(&target, &conf, &badblocks, target.leftbytes);
		else if ( check_bytes(block, &conf, target.leftbytes) == -1 )
			wipe_error(&target, &badblocks, target.leftbytes);
	}
	target.ptr = target.size;
	print_progress(&target);
	print_time(start_time);
	if ( badblocks.cnt > 0 ) {
		close(target.file);
		printf("All done but");
		print_bad_blocks(&badblocks);
		exit(1);
	}
	printf("Sample:\n");	// Read sample block(s) to show result
	print_block(&target, 0);
	if ( target.size >= 2048) print_block(&target, (target.size>>1)-256);
	if ( target.size >= 1024 ) print_block(&target, target.size-512);
	close(target.file);
	printf("Verification was succesfull, all done\n\n");
	exit(0);
}