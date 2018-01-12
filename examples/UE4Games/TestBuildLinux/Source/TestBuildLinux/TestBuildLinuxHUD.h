// Copyright 1998-2017 Epic Games, Inc. All Rights Reserved.

#pragma once 

#include "CoreMinimal.h"
#include "GameFramework/HUD.h"
#include "TestBuildLinuxHUD.generated.h"

UCLASS()
class ATestBuildLinuxHUD : public AHUD
{
	GENERATED_BODY()

public:
	ATestBuildLinuxHUD();

	/** Primary draw call for the HUD */
	virtual void DrawHUD() override;

private:
	/** Crosshair asset pointer */
	class UTexture2D* CrosshairTex;

};

