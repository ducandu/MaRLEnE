// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "Components/BillboardComponent.h"
#if WITH_EDITOR
#include "Editor/PropertyEditor/Public/IDetailCustomization.h"
#include "Editor/PropertyEditor/Public/DetailCategoryBuilder.h"
#include "Editor/PropertyEditor/Public/DetailLayoutBuilder.h"
#include "DetailWidgetRow.h"
#endif
#include "Engine/BlueprintGeneratedClass.h"
#include "MLObserver.generated.h"

UENUM(BlueprintType)		//"BlueprintType" is essential to include
enum class EObserverType : uint8
{
	Normal 	UMETA(DisplayName = "Normal"),
	Reward 	UMETA(DisplayName = "Reward (accum.)"),
	IsTerminal	UMETA(DisplayName = "Is-Terminal")
};

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
	UClass *Class;
};

#if WITH_EDITOR
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

	bool ObservableProp(UProperty *Prop, bool bShowPrivate);
};
#endif


UCLASS(ClassGroup = MaRLEnE, meta = (BlueprintSpawnableComponent), HideCategories(Mobility, Rendering, LOD, Collision, Physics, Activation, Cooking))
class MARLENE_API UMLObserver : public UActorComponent
{
	GENERATED_BODY()

public:
	// Sets default values for this component's properties
	UMLObserver();
	~UMLObserver();
	void OnRegister() override;
	void OnComponentDestroyed(bool bDestroyingHierarchy) override;

	UPROPERTY(EditAnywhere, Category = General)
	bool bEnabled;

	UPROPERTY(EditAnywhere, Category = Billboard)
	FVector BillboardLocation;

	UPROPERTY(EditAnywhere)
	bool bScreenCapture;

	UPROPERTY(EditAnywhere)
	bool bGrayscale;

	UPROPERTY(EditAnywhere)
	int32 Width;

	UPROPERTY(EditAnywhere)
	int32 Height;

	UPROPERTY(EditAnywhere)
	EObserverType ObserverType;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	bool bObserveLocation;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	bool bObserveRotation;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	bool bObserveScale;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	bool bObserveVisibility;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	bool bShowInheritedVariables;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	bool bShowPrivateVariables;

	UPROPERTY(EditAnywhere, Category = ObservedProperties)
	TArray<FMLObservedProperty> ObservedProperties;

	UFUNCTION()
	static TArray<UMLObserver *> GetRegisteredObservers();

	void PostEditChangeProperty(FPropertyChangedEvent & PropertyChangedEvent);

protected:
	// Called when the game starts
	virtual void BeginPlay() override;

	UBillboardComponent *BillboardComponent;


public:
	// Called every frame
	virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;


	UBlueprintGeneratedClass *GetBlueprintTemplate();
};
