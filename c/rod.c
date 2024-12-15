/* rod */
/* Written for POSIX + gcc */
/* Author: Markus Thilo */
/* E-mail: markus.thilo@gmail.com */
/* License: GPL-3 */
/* Version 0.0.1_2024-12-11 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

const int MAXLSBLK = 1024;
const int STRLEN = 32;
const int LISTLEN = 256;
const char *LSBLK = "lsblk -lno name";
const char *SETRO = "blockdev --setro ";
const int SLEEP = 10000;

int lsblk(char devs[LISTLEN][STRLEN]) {
	FILE *fp;
	int n = 0;
	fp = popen(LSBLK, "r"); if (fp == NULL) exit(1);
	while (fgets(devs[n], STRLEN, fp) != NULL) {
		for (int i=0; i<STRLEN; i++)
			if ( devs[n][i] == '\n' ) {
				devs[n][i] = 0;
				break;
			}
		n++;
	}
	pclose(fp);
	return n;
}

//int arrayswap(char target[LISTLEN][STRLEN], char source[LISTLEN][STRLEN], int n) {

int arraycpy(char target[LISTLEN][STRLEN], char source[LISTLEN][STRLEN], int n) {
	for (int i=0; i<n; i++) strcpy(target[i], source[i]);
	return n;
}


int main() {
	FILE *fp;
	char olddevs[LISTLEN][STRLEN], devs[LISTLEN][STRLEN], newdevs[LISTLEN][STRLEN];
	int old, n, new;
	old = lsblk(olddevs);
	printf("\nold = %d: ", old); for (int i=0; i<old; i++) printf("%s ", olddevs[i]); fflush(stdout);
	
	while ( 1 ) {
		n = lsblk(devs);
		if ( n < old ) old = arraycpy(olddevs, devs, n);
		else if ( n >= old ) {
			printf("\nn = %d: ", n); for (int i=0; i<n; i++) printf("%s ", devs[i]); fflush(stdout);

			
			new = arraycpy(newdevs, devs, n);
			//for (int i=0; i<n; i++) {
			//	new = 0;
				//for (int j=0; j<old; j++) if ( strcmp(devs[i], olddevs[j]) == 0 ) strcpy(newdevs[new++], devs[i]);
			printf("\nnew = %d: ", new); for (int i=0; i<new; i++) printf("%s ", newdevs[i]); fflush(stdout);
		}
		old = n;


		break;
		usleep(SLEEP);

	}
	
}