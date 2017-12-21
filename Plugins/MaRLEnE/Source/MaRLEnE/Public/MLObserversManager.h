// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "MLObserver.h"

/**
 * 
 */
class MARLENE_API MLObserversManager
{
public:
	static MLObserversManager &Get();

	static void RegisterObserver(UMLObserver *);
	static void UnregisterObserver(UMLObserver *);
	static TArray<UMLObserver *> GetObservers();

private:
	TArray<UMLObserver *> Observers;
};
