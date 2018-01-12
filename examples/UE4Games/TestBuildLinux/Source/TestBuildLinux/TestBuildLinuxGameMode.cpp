// Copyright 1998-2017 Epic Games, Inc. All Rights Reserved.

#include "TestBuildLinuxGameMode.h"
#include "TestBuildLinuxHUD.h"
#include "TestBuildLinuxCharacter.h"
#include "UObject/ConstructorHelpers.h"

ATestBuildLinuxGameMode::ATestBuildLinuxGameMode()
	: Super()
{
	// set default pawn class to our Blueprinted character
	static ConstructorHelpers::FClassFinder<APawn> PlayerPawnClassFinder(TEXT("/Game/FirstPersonCPP/Blueprints/FirstPersonCharacter"));
	DefaultPawnClass = PlayerPawnClassFinder.Class;

	// use our custom HUD class
	HUDClass = ATestBuildLinuxHUD::StaticClass();
}
