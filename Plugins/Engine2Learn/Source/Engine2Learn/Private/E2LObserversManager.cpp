// Fill out your copyright notice in the Description page of Project Settings.

#include "E2LObserversManager.h"

E2LObserversManager& E2LObserversManager::Get()
{
	static E2LObserversManager *ObserversManager = nullptr;
	if (!ObserversManager)
	{
		ObserversManager = new E2LObserversManager();
	}

	return *ObserversManager;
}

void E2LObserversManager::RegisterObserver(UE2LObserver *Observer)
{
	E2LObserversManager::Get().Observers.Add(Observer);
}

void E2LObserversManager::UnregisterObserver(UE2LObserver *Observer)
{
	E2LObserversManager::Get().Observers.Remove(Observer);
}

TArray<UE2LObserver *> E2LObserversManager::GetObservers()
{
	return E2LObserversManager::Get().Observers;
}

