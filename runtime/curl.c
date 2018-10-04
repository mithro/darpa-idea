#include <curl/curl.h>

#define GET_VAR(NAME) long get_ ## NAME (){return NAME;}
GET_VAR(CURL_GLOBAL_ALL)
GET_VAR(CURLOPT_URL)
GET_VAR(CURLOPT_VERBOSE)
GET_VAR(CURLOPT_WRITEFUNCTION)
GET_VAR(CURLOPT_WRITEDATA)
GET_VAR(CURLINFO_RESPONSE_CODE)