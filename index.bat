@echo off

REM Retrieve daily poetry to index.html
curl https://v1.jinrishici.com/all.txt > ./index.html

start git_push.bat