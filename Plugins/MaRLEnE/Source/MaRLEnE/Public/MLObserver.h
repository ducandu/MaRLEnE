// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "Components/BillboardComponent.h"
#include "Editor/PropertyEditor/Public/IDetailCustomization.h"
#include "Editor/PropertyEditor/Public/DetailCategoryBuilder.h"
#include "Editor/PropertyEditor/Public/DetailLayoutBuilder.h"
#include "MLObserver.generated.h"

USTRUCT()
struct FMLObservedProperty
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere)
	FString PropName;

	UPROPERTY(EditAnyWhere)
	bool bEnabled;

	FMLObservedProperty()
	{
		bEnabled = true;
	}

};

struct FMLPropertyItem
{
	FString Name;
	UObject *Object;
};

class FMLObservedPropertyDetails : public IPropertyTypeCustomization
{
public:
	static TSharedRef<IPropertyTypeCustomization> MakeInstance();

	virtual void CustomizeHeader(TSharedRef<class IPropertyHandle> StructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;
	virtual void CustomizeChildren(TSharedRef<class IPropertyHandle> StructPropertyHandle, class IDetailChildrenBuilder& StructBuilder, IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;

	TSharedRef<ITableRow> OnGenerateRowForProp(TSharedPtr<struct FMLPropertyItem> Item, const TSharedRef<STableViewBase>& OwnerTable);
	TSharedRef<SWidget> OnGenerateWidget(TSharedPtr<FMLPropertyItem> Item);

	void OnSelectionChanged(TSharedPtr<FMLPropertyItem> Item, ESelectInfo::Type SelectType);

	FText GetSelectedPropName() const;
	ECheckBoxState GetSelectedPropEnabled() const;

	void PropCheckChanged(ECheckBoxState CheckBoxState);

protected:
	TArray<TSharedPtr<FMLPropertyItem>> ParentProperties;

	FMLObservedProperty *ObservedProperty;
	UStructProperty *SProp;

	bool ObservableProp(UProperty *Prop);
};


UCLASS( ClassGroup=MaRLEnE, meta=(BlueprintSpawnableComponent), HideCategories(Mobility, Rendering, LOD, Collision, Physics, Activation, Cooking) )
class MARLENE_API UMLObserver : public USceneComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UMLObserver();

	~UMLObserver();

	UPROPERTY(EditAnywhere, Category = General)
	bool bEnabled;

	UPROPERTY(EditAnywhere)
	bool bScreenCapture;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	TArray<FMLObservedProperty> ObservedProperties;

	UPROPERTY(EditAnywhere)
	bool bUseActorProperties;

	UFUNCTION()
	static TArray<UMLObserver *> GetRegisteredObservers();

	void OnAttachmentChanged() override;

	void PostEditChangeProperty(FPropertyChangedEvent & PropertyChangedEvent);
	void OnComponentDestroyed(bool bDestroyingHierarchy);

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	UBillboardComponent *BillboardComponent;


public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

		
	
};
