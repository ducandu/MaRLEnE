// Copyright 1998-2017 Epic Games, Inc. All Rights Reserved.

#include "Engine2Learn.h"

#include "ISettingsModule.h"
#include "ISettingsSection.h"
#include "ISettingsContainer.h"

#include "DucanduSettings.h"

#define LOCTEXT_NAMESPACE "FEngine2LearnModule"

void FEngine2LearnModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module

	if (ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		// Create the new category
		ISettingsContainerPtr SettingsContainer = SettingsModule->GetContainer("Project");

		SettingsContainer->DescribeCategory("Ducandu",
			LOCTEXT("RuntimeWDCategoryName", "Ducandu"),
			LOCTEXT("RuntimeWDCategoryDescription", "Ducandu Project"));

		// Register the settings
		ISettingsSectionPtr SettingsSection = SettingsModule->RegisterSettings("Project", "Ducandu", "General",
			LOCTEXT("RuntimeGeneralSettingsName", "General"),
			LOCTEXT("RuntimeGeneralSettingsDescription", "General Options"),
			GetMutableDefault<UDucanduSettings>()
		);
	}
}

void FEngine2LearnModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

	if (ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		SettingsModule->UnregisterSettings("Project", "Ducandu", "General");
	}
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FEngine2LearnModule, Engine2Learn)