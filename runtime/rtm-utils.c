#include<sys/types.h>
#include<sys/stat.h>
#include<unistd.h>
#include<stdio.h>
#include<stdlib.h>
#include<dirent.h>
#include<pthread.h>
#include<sched.h>
#include<time.h>

//============================================================
//================== Directory Handling ======================
//============================================================

int get_file_type (char* filename) {
  struct stat filestat;
  if(stat(filename, &filestat) == 0){
    if(S_ISREG(filestat.st_mode))
      return 0;
    else if(S_ISDIR(filestat.st_mode))
      return 1;
    else
      return 2;    
  }
  else{
    return -1;
  }
}

int list_dir (char* filename, void (*f)(char*)){
  //Open directory
  DIR* dir = opendir(filename);
  if(dir == NULL) return -1;
  //Loop through directory entries
  while(1){
    //Read next entry
    struct dirent* entry = readdir(dir);
    if(entry == NULL){
      closedir(dir);
      return 0;
    }
    //Notify
    f(entry->d_name);
  }
}

//============================================================
//===================== Sleeping =============================
//============================================================

void sleep_us (long us){
  struct timespec t1, t2;
  t1.tv_sec = 0;
  t1.tv_nsec = us * 1000L;
  int ret = nanosleep(&t1, &t2);
  if(ret < 0){
    fprintf(stderr, "Sleep system call failed.\n");
    exit(-1);
  }
}
