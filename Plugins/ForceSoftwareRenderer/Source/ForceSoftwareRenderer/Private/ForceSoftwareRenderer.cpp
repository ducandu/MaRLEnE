// Copyright 1998-2017 Epic Games, Inc. All Rights Reserved.

#include "ForceSoftwareRenderer.h"

#define LOCTEXT_NAMESPACE "FForceSoftwareRendererModule"

void FForceSoftwareRendererModule::StartupModule()
{
	// This code will execute after your module is loaded into memory; the exact timing is specified in the .uplugin file per-module
	if (GRHIVendorId == 0x0)
	{
		UE_LOG(LogRHI, Warning, TEXT("Forcing GRHIVendorId to 0xFFFF"));
		GRHIVendorId = 0xFFFF;
	}
}

void FForceSoftwareRendererModule::ShutdownModule()
{
	// This function may be called during shutdown to clean up your module.  For modules that support dynamic reloading,
	// we call this function before unloading the module.
}

#undef LOCTEXT_NAMESPACE
	
IMPLEMENT_MODULE(FForceSoftwareRendererModule, ForceSoftwareRenderer)
