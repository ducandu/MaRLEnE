// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "MaRLEnESettings.generated.h"

/**
 * 
 */
UCLASS(config = Game, defaultconfig)
class MARLENE_API UMaRLEnESettings : public UObject
{
	GENERATED_BODY()
	
	UPROPERTY(EditAnywhere, config, Category = Network)
	FString Address;
	
	UPROPERTY(EditAnywhere, config, Category = Network)
	uint32 Port;
};
