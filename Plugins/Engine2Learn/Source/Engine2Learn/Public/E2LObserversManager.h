// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "E2LObserver.h"

/**
 * 
 */
class ENGINE2LEARN_API E2LObserversManager
{
public:
	static E2LObserversManager &Get();

	static void RegisterObserver(UE2LObserver *);
	static void UnregisterObserver(UE2LObserver *);
	static TArray<UE2LObserver *> GetObservers();

private:
	TArray<UE2LObserver *> Observers;
};
