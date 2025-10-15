# PowerShell install script for FlashCard
# Creates a virtual environment 'flash_cards', activates it, and installs requirements

$envName = "flash_cards"
$envPath = "./$envName"

python -m venv $envPath

# Activate the environment
$activateScript = "$envPath/Scripts/Activate.ps1"

Write-Host "Activating virtual environment..."
. $activateScript

Write-Host "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Setup complete."
Write-Host "Remember to install LAVFilters for multimedia support on Windows.  See README.md for details."
