// Fill out your copyright notice in the Description page of Project Settings.

#include "MLObserversManager.h"

MLObserversManager& MLObserversManager::Get()
{
	static MLObserversManager *ObserversManager = nullptr;
	if (!ObserversManager)
	{
		ObserversManager = new MLObserversManager();
	}

	return *ObserversManager;
}

void MLObserversManager::RegisterObserver(UMLObserver *Observer)
{
	MLObserversManager::Get().Observers.Add(Observer);
}

void MLObserversManager::UnregisterObserver(UMLObserver *Observer)
{
	MLObserversManager::Get().Observers.Remove(Observer);
}

TArray<UMLObserver *> MLObserversManager::GetObservers()
{
	return MLObserversManager::Get().Observers;
}

