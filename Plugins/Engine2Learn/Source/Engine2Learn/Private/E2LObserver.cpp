// Fill out your copyright notice in the Description page of Project Settings.

#include "E2LObserver.h"
#include "SlateExtras.h"
#include "SlateBasics.h"

#include "E2LObserversManager.h"

#include "DetailWidgetRow.h"

TSharedRef<IPropertyTypeCustomization> FE2LObservedPropertyDetails::MakeInstance()
{
	return MakeShareable(new FE2LObservedPropertyDetails);
}

TSharedRef<ITableRow> FE2LObservedPropertyDetails::OnGenerateRowForProp(TSharedPtr<struct FE2LPropertyItem> Item, const TSharedRef<STableViewBase>& OwnerTable)
{
	//Create the row
	return SNew(STableRow< TSharedPtr<struct FE2LPropertyItem> >, OwnerTable)
		.Padding(2.0f)
		[
			SNew(STextBlock).Text(FText::FromString(*Item.Get()->Name))
		];
}

TSharedRef<SWidget> FE2LObservedPropertyDetails::OnGenerateWidget(TSharedPtr<FE2LPropertyItem> Item)
{
	return SNew(STextBlock).Text(FText::FromString(Item->Name));
}

void FE2LObservedPropertyDetails::OnSelectionChanged(TSharedPtr<FE2LPropertyItem> Item, ESelectInfo::Type SelectType)
{
	ObservedProperty->PropName = Item->Name;
	SProp->MarkPackageDirty();
}

void FE2LObservedPropertyDetails::PropRangeMinChanged(float Value)
{
	ObservedProperty->RangeMin = Value;
}

void FE2LObservedPropertyDetails::PropRangeMaxChanged(float Value)
{
	ObservedProperty->RangeMax = Value;
}

void FE2LObservedPropertyDetails::PropCheckChanged(ECheckBoxState CheckBoxState)
{
	ObservedProperty->bEnabled = CheckBoxState == ECheckBoxState::Checked;
}

FText FE2LObservedPropertyDetails::GetSelectedPropName() const
{
	return FText::FromString(ObservedProperty->PropName);
}

ECheckBoxState FE2LObservedPropertyDetails::GetSelectedPropEnabled() const
{
	return ObservedProperty->bEnabled ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
}

TOptional<float> FE2LObservedPropertyDetails::GetSelectedPropRangeMin() const
{
	return ObservedProperty->RangeMin;
}

TOptional<float> FE2LObservedPropertyDetails::GetSelectedPropRangeMax() const
{
	return ObservedProperty->RangeMax;
}

void FE2LObservedPropertyDetails::CustomizeHeader(TSharedRef<class IPropertyHandle> StructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{

	TArray<UObject *> Objects;
	StructPropertyHandle->GetOuterObjects(Objects);

	if (Objects.Num() != 1)
		return;

	UE2LObserver *Observer = Cast<UE2LObserver>(Objects[0]);
	if (!Observer)
		return;

	UActorComponent *Parent = Observer->GetAttachParent();
	if (!Parent)
		return;

	SProp = Cast<UStructProperty>(StructPropertyHandle->GetProperty());
	if (!SProp)
		return;

	UScriptStruct *SSProp = Cast<UScriptStruct>(SProp->Struct);
	if (!SSProp)
		return;

	if (SSProp != FE2LObservedProperty::StaticStruct())
		return;

	ObservedProperty = SProp->ContainerPtrToValuePtr<FE2LObservedProperty>(StructPropertyHandle->GetValueBaseAddress((uint8 *)Observer));

	ParentProperties.Empty();

	TSharedPtr<FE2LPropertyItem> CurrentItem;

	for (TFieldIterator<UProperty> PropIt(Parent->GetClass()); PropIt; ++PropIt)
	{
		TSharedPtr<FE2LPropertyItem> PItem = TSharedPtr<FE2LPropertyItem>(new FE2LPropertyItem());
		PItem->Name = PropIt->GetName();
		PItem->Object = Parent;
		ParentProperties.Add(PItem);

		if (PItem->Name.Equals(ObservedProperty->PropName))
		{
			CurrentItem = PItem;
		}
	}



	HeaderRow.NameContent()
		[
			SNew(SComboBox<TSharedPtr<FE2LPropertyItem>>)
			.OptionsSource(&ParentProperties)
		.OnGenerateWidget(this, &FE2LObservedPropertyDetails::OnGenerateWidget)
		.OnSelectionChanged(this, &FE2LObservedPropertyDetails::OnSelectionChanged)
		.InitiallySelectedItem(CurrentItem)
		.Content()[
			SNew(STextBlock).Text(this, &FE2LObservedPropertyDetails::GetSelectedPropName)
		]
		]
	.ValueContent()
		[
			SNew(SHorizontalBox)

			+ SHorizontalBox::Slot().AutoWidth()
		[
			SNew(SCheckBox)
			.IsChecked(this, &FE2LObservedPropertyDetails::GetSelectedPropEnabled)
		.OnCheckStateChanged(this, &FE2LObservedPropertyDetails::PropCheckChanged)
		]
	+ SHorizontalBox::Slot().Padding(4).AutoWidth()
		[
			SNew(STextBlock).Text(FText::FromString("Min"))
		]
	+ SHorizontalBox::Slot().Padding(4).AutoWidth()
		[
			SNew(SNumericEntryBox<float>)
			.Value(this, &FE2LObservedPropertyDetails::GetSelectedPropRangeMin)
		.OnValueChanged(this, &FE2LObservedPropertyDetails::PropRangeMinChanged)
		]
	+ SHorizontalBox::Slot().Padding(4).AutoWidth()
		[
			SNew(STextBlock).Text(FText::FromString("Max"))
		]
	+ SHorizontalBox::Slot().Padding(4).AutoWidth()
		[
			SNew(SNumericEntryBox<float>)
			.Value(this, &FE2LObservedPropertyDetails::GetSelectedPropRangeMax)
		.OnValueChanged(this, &FE2LObservedPropertyDetails::PropRangeMaxChanged)
		]
		];
}

void FE2LObservedPropertyDetails::CustomizeChildren(TSharedRef<class IPropertyHandle> StructPropertyHandle, class IDetailChildrenBuilder& StructBuilder, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
	//Create further customization here
}


// Sets default values for this component's properties
UE2LObserver::UE2LObserver()
{

	E2LObserversManager::RegisterObserver(this);

	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;

	// ...

	BillboardComponent = CreateEditorOnlyDefaultSubobject<UBillboardComponent>(TEXT("Billboard"), true);
	BillboardComponent->Sprite = LoadObject<UTexture2D>(nullptr, TEXT("/Engine2Learn/Logo"));
	BillboardComponent->AttachToComponent(this, FAttachmentTransformRules::KeepRelativeTransform);

	bEnabled = true;
}

UE2LObserver::~UE2LObserver()
{
	// unregister from the manager
	E2LObserversManager::UnregisterObserver(this);
}

TArray<UE2LObserver *> UE2LObserver::GetRegisteredObservers()
{
	return E2LObserversManager::GetObservers();
}


// Called when the game starts
void UE2LObserver::BeginPlay()
{
	Super::BeginPlay();

	// ...

}


// Called every frame
void UE2LObserver::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

void UE2LObserver::OnAttachmentChanged()
{
	Super::OnAttachmentChanged();

	UE_LOG(LogTemp, Warning, TEXT("Parent changed to %s"), *GetOwner()->GetName());
}

