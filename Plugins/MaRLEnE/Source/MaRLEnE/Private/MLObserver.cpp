// Fill out your copyright notice in the Description page of Project Settings.

#include "MLObserver.h"
#include "SlateExtras.h"
#include "SlateBasics.h"

#include "MLObserversManager.h"



#if WITH_EDITOR
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


bool FMLObservedPropertyDetails::ObservableProp(UProperty *Prop, bool bShowPrivate)
{

	if (!bShowPrivate)
	{
		if (Prop->HasAnyPropertyFlags(CPF_DisableEditOnInstance))
		{
			return false;
		}
	}

	if (UArrayProperty *PArray = Cast<UArrayProperty>(Prop))
	{
		return ObservableProp(PArray->Inner, bShowPrivate);
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

	return false;
}

#endif

UBlueprintGeneratedClass *UMLObserver::GetBlueprintTemplate()
{
	UObject *Outer = GetOuter();
	for (UObject *CurrentOuter = Outer; CurrentOuter; CurrentOuter = CurrentOuter->GetOuter())
	{
		if (CurrentOuter->IsA<UBlueprintGeneratedClass>())
		{
			return (UBlueprintGeneratedClass *)CurrentOuter;
		}
	}
	return nullptr;
}

#if WITH_EDITOR
void FMLObservedPropertyDetails::CustomizeHeader(TSharedRef<class IPropertyHandle> StructPropertyHandle, class FDetailWidgetRow& HeaderRow, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{

	TArray<UObject *> Objects;
	StructPropertyHandle->GetOuterObjects(Objects);


	if (Objects.Num() != 1)
		return;


	UMLObserver *Observer = Cast<UMLObserver>(Objects[0]);
	if (!Observer)
		return;

	UClass *OwnerClass = nullptr;

	UObject *Owner = Observer->GetOwner();
	if (Owner)
	{
		OwnerClass = Owner->GetClass();
	}
	else
	{
		OwnerClass = Observer->GetBlueprintTemplate();
	}

	if (!OwnerClass)
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

	EFieldIteratorFlags::SuperClassFlags SuperFlags = EFieldIteratorFlags::SuperClassFlags::ExcludeSuper;

	if (Observer->bShowInheritedVariables)
	{
		SuperFlags = EFieldIteratorFlags::SuperClassFlags::IncludeSuper;
	}

	for (TFieldIterator<UProperty> PropIt(OwnerClass, SuperFlags); PropIt; ++PropIt)
	{
		if (!ObservableProp(*PropIt, Observer->bShowPrivateVariables))
		{
			continue;
		}
		TSharedPtr<FMLPropertyItem> PItem = TSharedPtr<FMLPropertyItem>(new FMLPropertyItem());
		PItem->Name = PropIt->GetName();
		PItem->Class = OwnerClass;
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
		.Content()
		[
			SNew(STextBlock).Text(this, &FMLObservedPropertyDetails::GetSelectedPropName)
		]
		]
	.ValueContent()
		[

			SNew(SCheckBox)
			.IsChecked(this, &FMLObservedPropertyDetails::GetSelectedPropEnabled)
		.OnCheckStateChanged(this, &FMLObservedPropertyDetails::PropCheckChanged)

		];
}

void FMLObservedPropertyDetails::CustomizeChildren(TSharedRef<class IPropertyHandle> StructPropertyHandle, class IDetailChildrenBuilder& StructBuilder, IPropertyTypeCustomizationUtils& StructCustomizationUtils)
{
	//Create further customization here
}
#endif


// Sets default values for this component's properties
UMLObserver::UMLObserver()
{

	// Set this component to be initialized when the game starts, and to be ticked every frame.  You can turn these features
	// off to improve performance if you don't need them.
	PrimaryComponentTick.bCanEverTick = false;

	// ...
	bEnabled = true;
	BillboardComponent = nullptr;
}

void UMLObserver::PostInitProperties()
{
	Super::PostInitProperties();
	MLObserversManager::RegisterObserver(this);
	UE_LOG(LogTemp, Warning, TEXT("Registered Observer at %p (owner %s)"), this, GetOwner() ? *GetOwner()->GetName() : nullptr);
}

void UMLObserver::OnRegister()
{
#if WITH_EDITOR
	AActor *Owner = GetOwner();
	if (Owner && Owner->GetRootComponent() && !BillboardComponent)
	{
		BillboardComponent = NewObject<UBillboardComponent>(Owner, NAME_None, RF_Transient);
		BillboardComponent->Sprite = LoadObject<UTexture2D>(nullptr, TEXT("/MaRLEnE/Logo"));
		BillboardComponent->Mobility = EComponentMobility::Movable;
		BillboardComponent->bHiddenInGame = true;
		BillboardComponent->bIsEditorOnly = true;
		BillboardComponent->SetupAttachment(Owner->GetRootComponent());
		BillboardComponent->RegisterComponent();
		BillboardComponent->SetRelativeLocation(BillboardLocation);
	}
#endif

	Super::OnRegister();
}

void UMLObserver::OnComponentDestroyed(bool bDestroyingHierarchy)
{

	Super::OnComponentDestroyed(bDestroyingHierarchy);

	if (BillboardComponent)
		BillboardComponent->DestroyComponent();



}

UMLObserver::~UMLObserver()
{
	// unregister from the manager
	UE_LOG(LogTemp, Warning, TEXT("Unregistered Observer %p"), this);
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
	//MLObserversManager::RegisterObserver(this);
}


// Called every frame
void UMLObserver::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	// ...
}

#if WITH_EDITOR
void UMLObserver::PostEditChangeProperty(FPropertyChangedEvent & PropertyChangedEvent)
{
	Super::PostEditChangeProperty(PropertyChangedEvent);


	if (BillboardComponent)
	{

		BillboardComponent->SetRelativeLocation(BillboardLocation);

	}

	FPropertyEditorModule& PropertyEditorModule = FModuleManager::GetModuleChecked<FPropertyEditorModule>("PropertyEditor");
	PropertyEditorModule.NotifyCustomizationModuleChanged();

}
#endif

