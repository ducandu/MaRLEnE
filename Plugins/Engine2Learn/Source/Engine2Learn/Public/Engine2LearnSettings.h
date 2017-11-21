// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "UObject/NoExportTypes.h"
#include "Engine2LearnSettings.generated.h"

/**
 * 
 */
UCLASS(config = Game, defaultconfig)
class ENGINE2LEARN_API UEngine2LearnSettings : public UObject
{
	GENERATED_BODY()
	
		UPROPERTY(EditAnywhere, config, Category = Custom)
		FString Address;
	
		UPROPERTY(EditAnywhere, config, Category = Custom)
		uint32 Port;
};
