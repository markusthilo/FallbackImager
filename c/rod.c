/* rod */
/* Written for POSIX + gcc */
/* Author: Markus Thilo */
/* E-mail: markus.thilo@gmail.com */
/* License: GPL-3 */
/* Version 0.0.1_2024-12-11 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

const int STRLEN = 256;
const int LISTLEN = 256;
const char *LSBLK = "lsblk -lno name";
const char *SETRO = "blockdev --setro ";

int main() {
	FILE *fp;
	char raw[STRLEN], dev[STRLEN], olddevs[LISTLEN][STRLEN], newdevs[LISTLEN][STRLEN];
	int old = 0, new;
	fp = popen(LSBLK, "r"); if (fp == NULL) exit(1);
	while (fgets(raw, sizeof(raw), fp) != NULL)
		for (int i=0; i<sizeof(raw); i++) if (raw[i] != '\n') olddevs[old][i] = raw[i];
			else { olddevs[old++][i] = 0; break; }
	pclose(fp);

	for (int i=0; i<old; i++) printf("%s ", olddevs[i]);

	fp = popen(LSBLK, "r"); if (fp == NULL) exit(1);
	new = 0;
	while (fgets(raw, sizeof(raw), fp) != NULL)
		for (int i=0; i<sizeof(raw); i++) {
			if (raw[i] != '\n') newdevs[new][i] = raw[i];
			else { newdevs[new++][i] = 0; break; }
		}
	pclose(fp);

	for (int i=0; i<new; i++) printf("%s ", newdevs[i]);

	exit(0);
}