# PowerShell run script for FlashCard
# Activates 'flash_cards' environment and runs flashcards.py

$envPath = "./flash_cards"
$activateScript = "$envPath/Scripts/Activate.ps1"

. $activateScript
python flashcards.py
