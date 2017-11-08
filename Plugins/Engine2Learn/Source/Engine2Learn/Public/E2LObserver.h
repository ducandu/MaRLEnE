// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "Components/BillboardComponent.h"
#include "Editor/PropertyEditor/Public/IDetailCustomization.h"
#include "Editor/PropertyEditor/Public/DetailCategoryBuilder.h"
#include "Editor/PropertyEditor/Public/DetailLayoutBuilder.h"
#include "E2LObserver.generated.h"

UENUM()
enum class EE2LDataTypeEnum : uint8
{
    E2L_DATATYPE_BOOL,  // a bool type
    E2L_DATATYPE_INT,  // some int type (uint32, etc..)
    E2L_DATATYPE_FLOAT,  // some float type (double, float, etc..)
    // the last item in an enum always HAS to be 'num_items' for us to be able to retrieve the len of the enum
    E2L_DATATYPE_ENUM,  // an int based enum (like this one here);
    E2L_DATATYPE_CAM  // a camera output (3D-tensor, w x h x color-depth)
};

USTRUCT()
struct FE2LObservedProperty
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere)
	FString PropName;

	UPROPERTY(EditAnyWhere)
	bool bEnabled;

	FE2LObservedProperty()
	{
		bEnabled = true;
	}

	// get rid of this prop
	UPROPERTY(EditAnyWhere)
	float RangeMin;
	// get rid of this prop
	UPROPERTY(EditAnyWhere)
	float RangeMax;

	UPROPERTY(EditAnyWhere)
	EE2LDataTypeEnum DataType;

	UPROPERTY(EditAnyWhere)
	uint32 Len;
};

struct FE2LPropertyItem
{
	FString Name;
	UObject *Object;
};

class FE2LObservedPropertyDetails : public IPropertyTypeCustomization
{
public:
	static TSharedRef<IPropertyTypeCustomization> MakeInstance();

	virtual void CustomizeHeader(TSharedRef<class IPropertyHandle> StructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;
	virtual void CustomizeChildren(TSharedRef<class IPropertyHandle> StructPropertyHandle, class IDetailChildrenBuilder& StructBuilder, IPropertyTypeCustomizationUtils& StructCustomizationUtils) override;

	TSharedRef<ITableRow> OnGenerateRowForProp(TSharedPtr<struct FE2LPropertyItem> Item, const TSharedRef<STableViewBase>& OwnerTable);
	TSharedRef<SWidget> OnGenerateWidget(TSharedPtr<FE2LPropertyItem> Item);

	void OnSelectionChanged(TSharedPtr<FE2LPropertyItem> Item, ESelectInfo::Type SelectType);

	FText GetSelectedPropName() const;
	ECheckBoxState GetSelectedPropEnabled() const;
	TOptional<float> GetSelectedPropRangeMin() const;
	TOptional<float> GetSelectedPropRangeMax() const;

	void PropRangeMinChanged(float Value);
	void PropRangeMaxChanged(float Value);
	void PropCheckChanged(ECheckBoxState CheckBoxState);

protected:
	TArray<TSharedPtr<FE2LPropertyItem>> ParentProperties;

	FE2LObservedProperty *ObservedProperty;
	UStructProperty *SProp;
};


UCLASS( ClassGroup=Engine2Learn, meta=(BlueprintSpawnableComponent), HideCategories(Mobility, Rendering, LOD, Collision, Physics, Activation, Cooking) )
class ENGINE2LEARN_API UE2LObserver : public USceneComponent
{
	GENERATED_BODY()

public:	
	// Sets default values for this component's properties
	UE2LObserver();

	~UE2LObserver();

	UPROPERTY(EditAnywhere, Category = General)
	bool bEnabled;

	UPROPERTY(EditAnywhere)
	bool bScreenCapture;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	TArray<FE2LObservedProperty> ObservedProperties;

	UFUNCTION()
	static TArray<UE2LObserver *> GetRegisteredObservers();

	void OnAttachmentChanged() override;


protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	UBillboardComponent *BillboardComponent;


public:	
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

		
	
};
