$VERYPDF_HOME="C:\ProgramFiles\pdf2txtocrcmd"
$CURRENT_LOC=$MyInvocation.MyCommand.Path
$CURRENT_LOC = $CURRENT_LOC.Replace("ocr_1image.ps1", "")
# echo $CURRENT_LOC

$inputfile=$args[0]

$output="output"
#$input="ocr_test"
#$output="ocr_test_out"

# echo ${VERYPDF_HOME}\${input}
cd ${VERYPDF_HOME}

# $starttime=Get-Date

# Run OCR for 1 file in the directory

# echo "Processing $inputfile"

# Remove output file if it exists
# Because pdr2txtocr.exe will append results to existing files
# Let it go if not exist
Remove-Item $CURRENT_LOC$inputfile.txt -ea SilentlyContinue 

#Call the VeryPDF commercial software
echo ".\pdf2txtocr.exe -ocr $CURRENT_LOC$inputfile $CURRENT_LOC$inputfile.txt"
.\pdf2txtocr.exe -ocr $CURRENT_LOC$inputfile $CURRENT_LOC$inputfile.txt

# $endtime=Get-Date
# echo $starttime
# echo $endtime
# echo "TotalTime in Seconds " ($endtime-$starttime).TotalSeconds

cd $CURRENT_LOC
