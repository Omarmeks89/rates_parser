# Description
A simple project for parsing logistics service rates.
Turns a string like:
> Xiamen	Changsha	Alashankou	Moscow	$9,500 	The early of Dec

or
> Tianjin-Vladivostok $3100/5200/5200 by huaxin Excluded DTHC$250/300

to table looks like this:
[![2023-05-14-20-11-58.png](https://i.postimg.cc/Z5LzkDRG/2023-05-14-20-11-58.png)](https://postimg.cc/YvjsYRQR)

The project was done quickly, since the manual processing of such unstructured files took a very long time.

## Quickstart
When you need to load and parse multimodal rates
have to use flag [ --m ], for using specific table headers
preset. (it`s configured in .env file)
```bash
loadfile /path.txt --m newtxtfile
loadfile /path.xlsx --m newexcelfile
```
Railway rates are specified by flag [ --r ]:
```bash
loadfile /path.txt --r newfile
loadfile /path.xlsx --r newexcelfile
```
In general command structure is:
```bash
[cmd_name] [mode_flag] [path] [pattern] [tmp_filename]
```
After loading file storing in cache by [tmp_filename], 
that in [savefile] command is using for create worksheet
in excel file.
```bash
showprev newexcelfile
```
```bash
savefile /new_path.xlsx newexcelfile
```

Command [showprev] is using for display file preview
(as was shown at screenshot)
[![2023-05-14-21-16-09.png](https://i.postimg.cc/HWt4m557/2023-05-14-21-16-09.png)](https://postimg.cc/rzKtCDf8)

Each command specified by tokens, that can`be validated on
program bootstrap. Program give you opportunity to specify
your own command syntax you like.

Next step is reducing tech debt.

## Realized
Commands
```bash
loadfile
showprev
savefile
```
Now program can operate with .txt and .xlsx files [for loading]
and .xlsx files only for saving (in reason that .txt files
don`t use for the next operations with rates). But it`s simple to
realise.

## In progress
Next version will`be realised:
```bash
showcached
```
to display elements [names] stored in cache
```bash
exit
```
and other shutdown operations, now programm finished
with Ctrl+C only, ha-ha (it`s awful, i know...)

## Packages
I use
```bash
pytest
```
for testing and
```bash
openpyxl
```
for operations with excel files.

So, like that at the moment.
