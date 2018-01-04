// Fill out your copyright notice in the Description page of Project Settings.

#include "MLObserver.h"
#include "SlateExtras.h"
#include "SlateBasics.h"

#include "MLObserversManager.h"

#include "DetailWidgetRow.h"

TSharedRef<IPropertyTypeCustomization> FMLObservedPropertyDetails::MakeInstance()
{
	return MakeShareable(new FMLObservedPropertyDetails);
}

TSharedRef<ITableRow> FMLObservedPropertyDetails::OnGenerateRowForProp(TSharedPtr<struct FMLPropertyItem> Item, const TSharedRef<STableViewBase>& OwnerTable)
{
	//Create the row
	return SNew(STableRow< TSharedPtr<struct FMLPropertyItem> >, OwnerTable)
		.Padding(2.0f)
		[
			SNew(STextBlock).Text(FText::FromString(*Item.Get()->Name))
		];
}

TSharedRef<SWidget> FMLObservedPropertyDetails::OnGenerateWidget(TSharedPtr<FMLPropertyItem> Item)
{
	return SNew(STextBlock).Text(FText::FromString(Item->Name));
}

void FMLObservedPropertyDetails::OnSelectionChanged(TSharedPtr<FMLPropertyItem> Item, ESelectInfo::Type SelectType)
{
	ObservedProperty->PropName = Item->Name;
	SProp->MarkPackageDirty();
}


void FMLObservedPropertyDetails::PropCheckChanged(ECheckBoxState CheckBoxState)
{
	ObservedProperty->bEnabled = CheckBoxState == ECheckBoxState::Checked;
}

FText FMLObservedPropertyDetails::GetSelectedPropName() const
{
	return FText::FromString(ObservedProperty->PropName);
}

ECheckBoxState FMLObservedPropertyDetails::GetSelectedPropEnabled() const
{
	return ObservedProperty->bEnabled ? ECheckBoxState::Checked : ECheckBoxState::Unchecked;
}


bool FMLObservedPropertyDetails::ObservableProp(UProperty *Prop)
{

	

	if (Prop->GetName() == "RelativeLocation")
	{

		if (UStructProperty *SProp = Cast<UStructProperty>(Prop))
		{
			if (UScriptStruct *SSProp = Cast<UScriptStruct>(SProp->Struct))
			{
				if (SSProp == TBaseStructure<FVector>::Get())
					return true;
			}

		}
	}

	if (Prop->GetName() == "RelativeRotation")
	{

		if (UStructProperty *SProp = Cast<UStructProperty>(Prop))
		{
			if (UScriptStruct *SSProp = Cast<UScriptStruct>(SProp->Struct))
			{
				if (SSProp == TBaseStructure<FRotator>::Get())
					return true;
			}

		}
	}

	if (Prop->GetName() == "RelativeScale3D")
	{

		if (UStructProperty *SProp = Cast<UStructProperty>(Prop))
		{
			if (UScriptStruct *SSProp = Cast<UScriptStruct>(SProp->Struct))
			{
				if (SSProp == TBaseStructure<FVector>::Get())
					return true;
			}

		}
	}

	if (Prop->GetName() == "bVisible")
	{

		if (UBoolProperty *SProp = Cast<UBoolProperty>(Prop))
		{
			return true;

		}
	}

	if (!Prop->HasAllPropertyFlags(CPF_DisableEditOnInstance))
	{
		return true;
	}

	/*
	if (UArrayProperty *PArray = Cast<UArrayProperty>(Prop))
	{
		return ObservableProp(PArray->Inner);
	}

	if (Prop->IsA<UBoolProperty>())
		return true;
	if (Prop->IsA<UFloatProperty>())
		return true;
	if (Prop->IsA<UIntProperty>())
		return true;
	if (Prop->IsA<UUInt64Property>())
		return true;
	if (Prop->IsA<UInt64Property>())
		return true;
	if (Prop->IsA<UEnumProperty>())
		return true;

	if (UStructProperty *SProp = Cast<UStructProperty>(Prop))
	{
		if (UScriptStruct *SSProp = Cast<UScriptStruct>(SProp->Struct))
		{
			if (SSProp == TBaseStructure<FVector>::Get())
				return true;
			if (SSProp == TBaseStructure<FRotator>::Get())
				return true;
		}

	}
	*/

	return false;
}

void FMLObservedPropertyDetails::CustomizeHeader(TSharedRef<class IPropertyHandle> StructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{

	TArray<UObject *> Objects;
	StructPropertyHandle->GetOuterObjects(Objects);

	if (Objects.Num() != 1)
		return;

	UMLObserver *Observer = Cast<UMLObserver>(Objects[0]);
	if (!Observer)
		return;

	UObject *Parent = Observer->GetAttachParent();

	/*
	UObject *Parent = nullptr;

	if (!Observer->bUseActorProperties)
	{
		Parent = Observer->GetAttachParent();
	}
	else
	{
		Parent = Observer->GetOwner();
	}
	*/

	if (!Parent)
		return;


	SProp = Cast<UStructProperty>(StructPropertyHandle->GetProperty());
	if (!SProp)
		return;

	UScriptStruct *SSProp = Cast<UScriptStruct>(SProp->Struct);
	if (!SSProp)
		return;

	if (SSProp != FMLObservedProperty::StaticStruct())
		return;

	ObservedProperty = SProp->ContainerPtrToValuePtr<FMLObservedProperty>(StructPropertyHandle->GetValueBaseAddress((uint8 *)Observer));

	ParentProperties.Empty();

	TSharedPtr<FMLPropertyItem> CurrentItem;



	for (TFieldIterator<UProperty> PropIt(Parent->GetClass()); PropIt; ++PropIt)
	{
		if (!ObservableProp(*PropIt))
		{
			continue;
		}
		TSharedPtr<FMLPropertyItem> PItem = TSharedPtr<FMLPropertyItem>(new FMLPropertyItem());
		PItem->Name = PropIt->GetName();
		PItem->Object = Parent;
		ParentProperties.Add(PItem);

		if (PItem->Name.Equals(ObservedProperty->PropName))
		{
			CurrentItem = PItem;
		}
	}

	ParentProperties.Sort([](const TSharedPtr<FMLPropertyItem>& One, const TSharedPtr<FMLPropertyItem>& Two)
	{
		return One->Name < Two->Name;
	});

	HeaderRow.NameContent()
		[
			SNew(SComboBox<TSharedPtr<FMLPropertyItem>>)
			.OptionsSource(&ParentProperties)
		.OnGenerateWidget(this, &FMLObservedPropertyDetails::OnGenerateWidget)
		.OnSelectionChanged(this, &FMLObservedPropertyDetails::OnSelectionChanged)
		.InitiallySelectedItem(CurrentItem)
		.Content()[
			SNew(STextBlock).Text(this, &FMLObservedPropertyDetails::GetSelectedPropName)
		]
		]
	.ValueContent()
		[
			SNew(SHorizontalBox)

			+ SHorizontalBox::Slot().AutoWidth()
		[
			SNew(SCheckBox)
			.IsChecked(this, &FMLObservedPropertyDetails::GetSelectedPropEnabled)
		.OnCheckStateChanged(this, &FMLObservedPropertyDetails::PropCheckChanged)
		]
		];
}

void FMLObservedPropertyDetails::CustomizeChildren(TSharedRef<class IPropertyHandle> StructPropertyHandle, class IDetailChildrenBuilder& StructBuilder, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
	//Create further customization here
}


// Sets default values for this component's properties
UMLObserver::UMLObserver()
{

	MLObserversManager::RegisterObserver(this);

	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;

	// ...

	BillboardComponent = CreateEditorOnlyDefaultSubobject<UBillboardComponent>(TEXT("Billboard"), true);
	BillboardComponent->Sprite = LoadObject<UTexture2D>(nullptr, TEXT("/MaRLEnE/Logo"));
	BillboardComponent->AttachToComponent(this, FAttachmentTransformRules::KeepRelativeTransform);

	bEnabled = true;
}

UMLObserver::~UMLObserver()
{
	// unregister from the manager
	MLObserversManager::UnregisterObserver(this);
}

TArray<UMLObserver *> UMLObserver::GetRegisteredObservers()
{
	return MLObserversManager::GetObservers();
}


// Called when the game starts
void UMLObserver::BeginPlay()
{
	Super::BeginPlay();

	// ...

}


// Called every frame
void UMLObserver::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

void UMLObserver::OnComponentDestroyed(bool bDestroyingHierarchy)
{
	MLObserversManager::UnregisterObserver(this);
}

void UMLObserver::OnAttachmentChanged()
{
	Super::OnAttachmentChanged();

	USceneComponent *Parent = GetAttachParent();
	if (Parent)
	{
		UE_LOG(LogTemp, Warning, TEXT("Parent changed to %s"), *Parent->GetName());
	}
}

void UMLObserver::PostEditChangeProperty(FPropertyChangedEvent & PropertyChangedEvent)
{

	FPropertyEditorModule& PropertyEditorModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");
	PropertyEditorModule.NotifyCustomizationModuleChanged();
}

