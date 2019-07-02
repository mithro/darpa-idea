#include<sys/types.h>
#include<sys/stat.h>
#include<unistd.h>
#include<stdio.h>
#include<stdlib.h>
#include<string.h>
#include<dirent.h>
#include<pthread.h>
#include<sched.h>
#include<time.h>

//============================================================
//===================== String List ==========================
//============================================================

typedef struct {
  int n;
  int capacity;
  char** strings;
} StringList;

StringList* make_stringlist (int capacity){
  StringList* list = (StringList*)malloc(sizeof(StringList));
  list->n = 0;
  list->capacity = capacity;
  list->strings = malloc(capacity * sizeof(char*));
  return list;
}

void ensure_stringlist_capacity (StringList* list, int c) {
  if(list->capacity < c){
    int new_capacity = list->capacity;
    while(new_capacity < c) new_capacity *= 2;
    char** new_strings = malloc(new_capacity * sizeof(char*));
    memcpy(new_strings, list->strings, list->n * sizeof(char*));
    list->capacity = new_capacity;
    free(list->strings);
    list->strings = new_strings;
  }
}

void free_stringlist (StringList* list){
  for(int i=0; i<list->n; i++)
    free(list->strings[i]);
  free(list->strings);
  free(list);
}

void stringlist_add (StringList* list, char* string){
  ensure_stringlist_capacity(list, list->n + 1);
  char* copy = malloc(strlen(string) + 1);
  strcpy(copy, string);
  list->strings[list->n] = copy;
  list->n++;
}

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

//int list_dir (char* filename, void (*f)(char*)){
//  //Open directory
//  DIR* dir = opendir(filename);
//  if(dir == NULL) return -1;
//  //Loop through directory entries
//  while(1){
//    //Read next entry
//    struct dirent* entry = readdir(dir);
//    if(entry == NULL){
//      closedir(dir);
//      return 0;
//    }
//    //Notify
//    f(entry->d_name);
//  }
//}

StringList* list_dir (char* filename){
  //Open directory
  DIR* dir = opendir(filename);
  if(dir == NULL) return 0;
  
  //Allocate memory for strings
  StringList* list = make_stringlist(10);
  //Loop through directory entries
  while(1){
    //Read next entry
    struct dirent* entry = readdir(dir);
    if(entry == NULL){
      closedir(dir);
      return list;
    }
    //Notify
    stringlist_add(list, entry->d_name);
  }

  free(list);
  return 0;
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
