#!powershell

# WANT_JSON
# POWERSHELL_COMMON

########

function Get-ComputerName() {
    Get-Content env:computername
    return
}

function Set-ComputerName($newComputerName) {
    $systemInfo = Get-WmiObject Win32_ComputerSystem
    $cmdResult = $systemInfo.Rename($newComputerName)
    if ($cmdResult.ReturnValue -ne 0) {
        Fail-Json $result "The computer name could not be set. Check that it is a valid name."
    }
}

########

$params = Parse-Args $args;

$result = New-Object psobject @{
    changed = $false
};

If (-not $params.name.GetType)
{
    Fail-Json $result "missing required arguments: name"
}

$newComputerName = Get-Attr $params "name"
$currentComputerName = (Get-ComputerName)

if ($newComputerName -ne $currentComputerName) {
    $setResult = (Set-ComputerName($newComputerName))
    $result.changed = $true
}

# Set-Attr $result "user" $user_obj
Set-Attr $result "computer_name" $newComputerName

Exit-Json $result;
