@echo off

REM Add files to the staging area
git add .

REM Commit changes to the local repository
git commit -m "Daily poetry"

REM Push changes to the remote repository
git push https://github.com/liuchenyang0703/Daily_Poems.git master:main

REM Display completion message
echo Commit completed!

REM Pause to wait for user input before closing the command prompt
pause