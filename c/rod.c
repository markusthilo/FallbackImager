/* rod */
/* Written for POSIX + gcc */
/* Author: Markus Thilo */
/* E-mail: markus.thilo@gmail.com */
/* License: GPL-3 */
/* Version 0.0.1_2024-12-18 */

/* Endless loop to set all new attached block devices to read only using lsblk and blockdev --setro */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

const int STRLEN = 256;		// device names cannot be larger (e.g. nvme0n1p1  
const int LISTLEN = 256;	// if you have morer blockdevices, there will be a problem
const char *DISKSTATS = "/proc/diskstats";	// here are the blockdevices lsited
const int SKIP = 13;	// number of chars to skip to get device name 
const char *SETRO = "blockdev --setro /dev/";	// execute this to set read-only
const int SLEEP = 10000;	// microseconds to wait before next check

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
int main() {
	FILE *fh;
	fh = fopen(DISKSTATS, "r");
	char olddevs[LISTLEN][STRLEN], devs[LISTLEN][STRLEN], newdevs[LISTLEN][STRLEN];
	int old, n, new;
	old = lsblk(olddevs, fh);
	if ( old == -1 ) { fprintf(stderr, "ERROR while running lsblk\n"); exit(-1); }
	while ( 1 ) {
		new = 0;
		n = lsblk(devs, fh);
		if ( n == -1 ) { printf("WARNING: a problem occured while running lsblk"); n = old; }
		if ( n == old ) { usleep(SLEEP); continue; }
		if ( n > old )
			for (int i=0; i<n; i++)
				if ( inarray(devs[i], olddevs, old) == -1 ) {
					if ( setro(devs[i]) != 0 ) printf("WARNING: unable to set %s read-only\n", devs[i]);
					else printf("Setting %s to read-only\n", devs[i]); fflush(stdout);
				}
		old = arraycpy(olddevs, devs, n);
	}
}