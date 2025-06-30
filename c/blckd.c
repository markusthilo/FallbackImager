/* blckd */
/* Written for POSIX + gcc */
/* Author: Markus Thilo */
/* E-mail: markus.thilo@gmail.com */
/* License: GPL-3 */
/* Endless loop to check for new block devices and set to read only */
/* uses: */
/* blockdev --setro */

/* Version */
const char *VERSION = "0.0.1_2025-06-30";

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

const int STRLEN = 256;		// device names cannot be larger (e.g. nvme0n1p1  
const int LISTLEN = 256;	// if you have morer blockdevices, there will be a problem
const char *DISKSTATS = "/proc/diskstats";	// here are the blockdevices listed
const int SKIP = 13;	// number of chars to skip to get device name 
const char *SETRO = "blockdev --setro /dev/";	// execute this to set read-only
const int SLEEP = 10000;	// microseconds to wait before next check

/* Print help text */
void help(const int r) {
	printf(" _     _      _       _\n");
	printf("| |__ | | ___| | ____| |\n");
	printf("| '_ \\| |/ __| |/ / _` |\n");
	printf("| |_) | | (__|   < (_| |\n");
	printf("|_.__/|_|\\___|_|\\_\\__,_|\n\n");
	printf("v%s\n\n", VERSION);
	printf("Endless loop to check for new block devices and set to read only\n\n");
	printf("Usage:\n");
	printf("blckd [OPTION]\n\n");
	printf("OPTION:\n");
	printf("    -h / --help  : print this help\n");
	printf("    -r / --setro : set new block devices to read only\n\n");
	printf("Default: print new devices to stdout, do not set to read only\n\n");
	printf("Disclaimer:\n");
	printf("The author is not responsible for any loss of data.\n");
	printf("Obviously, this tool is dangerous as it is designed to erase data.\n\n");
	printf("Author: Markus Thilo\n");
	printf("License: GPL-3\n");
	printf("This CLI tool is part of the FallbackImager project:\n");
	printf("https://github.com/markusthilo/FallbackImager\n\n");
	exit(r);
}

/* Get block device names without \n in array of strings */
int lsblk(char devs[LISTLEN][STRLEN], FILE *fh) {
	int len, n = 0;
	char line[STRLEN];
	if ( fh < 0 ) return -1;
	while ( fgets(line, STRLEN, fh) > 0 ) {
		len = 0;
		for (int i=SKIP; i<STRLEN; i++)
			if ( line[i] == ' ' ) { devs[n][len] = 0; break; }
			else { devs[n][len++] = line[i]; }
		n++;
	}
	rewind(fh);
	return n;
}

/* Set block device to read only */
int setro(char dev[STRLEN]) {
	char cmd[sizeof(SETRO) + STRLEN];
	strcpy(cmd, SETRO);
    strcat(cmd, dev);
	return system(cmd);
}

/* Copy array of strings to another array of strings */
int arraycpy(char target[LISTLEN][STRLEN], char source[LISTLEN][STRLEN], int n) {
	for (int i=0; i<n; i++) strcpy(target[i], source[i]);
	return n;
}

/* Check if string is in array of strings */
int inarray(char string[STRLEN], char array[LISTLEN][STRLEN], int n) {
	for (int i=0; i<n; i++) if ( strcmp(string, array[i]) == 0 ) return i;
	return -1;
}

/* Main loop */
int main(int argc, char **argv) {
	int ro_flag = 0;	// flag for what to do on new block device
	if ( argc == 2 ) {
		if ( ( strcmp(argv[1], "-h") == 0 ) || ( strcmp(argv[1], "--help") == 0 ) ) help(0);
		if ( ( strcmp(argv[1], "-r") == 0 ) || ( strcmp(argv[1], "--setro") == 0 ) ) ro_flag = 1;
		else help(1);
	} else if ( argc > 1 ) help(1);
	FILE *fh;
	fh = fopen(DISKSTATS, "r");
	char olddevs[LISTLEN][STRLEN], devs[LISTLEN][STRLEN], newdevs[LISTLEN][STRLEN];
	int old, n;
	old = lsblk(olddevs, fh);
	if ( old == -1 ) { fprintf(stderr, "ERROR while running lsblk\n"); exit(-1); }
	while ( 1 ) {
		usleep(SLEEP);
		n = lsblk(devs, fh);
		if ( n < 0 ) {
			fprintf(stderr, "ERROR: a problem occured while reading %s", DISKSTATS);
			exit(n);
		}
		if ( n < old ) printf("Block device had been detached\n");
		else if ( n > old )
			for (int i=0; i<n; i++)
				if ( inarray(devs[i], olddevs, old) == -1 )
					if ( ro_flag == 0 ) printf("New block device %s\n", devs[i]);
					else {
						if ( setro(devs[i]) != 0 ) {
							fprintf(stderr, "WARNING: could not set %s to read-only\n", devs[i]);
							fflush(stderr);
						} else printf("Setting new block device %s to read-only\n", devs[i]);
					}
		fflush(stdout);
		old = arraycpy(olddevs, devs, n);
	}
}