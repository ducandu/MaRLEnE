// Copyright 1998-2017 Epic Games, Inc. All Rights Reserved.

#include "MaRLEnE.h"

#if WITH_EDITOR
#include "ISettingsModule.h"
#include "ISettingsSection.h"
#include "ISettingsContainer.h"
#include "PropertyEditorModule.h"
#endif

#include "MaRLEnESettings.h"
#include "MLObserver.h"

#define LOCTEXT_NAMESPACE "FMaRLEnEModule"

void FMaRLEnEModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
#if WITH_EDITOR
	if (ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		// Create the new category
		ISettingsContainerPtr SettingsContainer = SettingsModule->GetContainer("Project");

		SettingsContainer->DescribeCategory("MaRLEnE",
			LOCTEXT("RuntimeWDCategoryName", "Machine Learning"),
			LOCTEXT("RuntimeWDCategoryDescription", "Machine Learning - MaRLEnE"));

		// Register the settings
		ISettingsSectionPtr SettingsSection = SettingsModule->RegisterSettings("Project", "MaRLEnE", "General",
			LOCTEXT("RuntimeGeneralSettingsName", "General"),
			LOCTEXT("RuntimeGeneralSettingsDescription", "Network/TCP Options"),
			GetMutableDefault<UMaRLEnESettings>()
		);
	}

	if (FPropertyEditorModule *PropertyModule = FModuleManager::GetModulePtr<FPropertyEditorModule>("PropertyEditor"))
	{

		//Custom detail views
		PropertyModule->RegisterCustomPropertyTypeLayout("MLObservedProperty", FOnGetPropertyTypeCustomizationInstance::CreateStatic(&FMLObservedPropertyDetails::MakeInstance));
	}
#endif
}

void FMaRLEnEModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.

#if WITH_EDITOR
	if (ISettingsModule* SettingsModule = FModuleManager::GetModulePtr<ISettingsModule>("Settings"))
	{
		SettingsModule->UnregisterSettings("Project", "MaRLEnE", "General");
	}

	if (FPropertyEditorModule *PropertyModule = FModuleManager::GetModulePtr<FPropertyEditorModule>("PropertyEditor"))
	{
		PropertyModule->UnregisterCustomPropertyTypeLayout("MLObservedProperty");
	}
#endif
}

#undef LOCTEXT_NAMESPACE

IMPLEMENT_MODULE(FMaRLEnEModule, MaRLEnE)