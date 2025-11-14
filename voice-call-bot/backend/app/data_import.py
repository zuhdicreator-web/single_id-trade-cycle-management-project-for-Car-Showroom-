import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
from app import models, crud, schemas
from app.database import SessionLocal

def import_sales_data(excel_path: str, db: Session):
    """
    Import sales data from Excel file
    """
    print(f"Reading sales data from {excel_path}...")
    df = pd.read_excel(excel_path, sheet_name=0)
    
    print(f"Found {len(df)} records")
    
    imported_customers = 0
    imported_vehicles = 0
    
    for idx, row in df.iterrows():
        try:
            # Check if customer exists
            customer = crud.get_customer_by_single_id(db, single_id=str(row['SINGLE ID']))
            
            if not customer:
                # Create customer
                customer_data = schemas.CustomerCreate(
                    single_id=str(row['SINGLE ID']),
                    nik=str(row['NIK']),
                    name=str(row['CUSTOMER']),
                    phone=str(row.get('TLP/HP', '')) if pd.notna(row.get('TLP/HP')) else None,
                    address=str(row.get('ALAMAT1', '')) if pd.notna(row.get('ALAMAT1')) else None,
                    kelurahan=str(row.get('KELURAHAN', '')) if pd.notna(row.get('KELURAHAN')) else None,
                    kecamatan=str(row.get('KECAMATAN', '')) if pd.notna(row.get('KECAMATAN')) else None
                )
                customer = crud.create_customer(db, customer=customer_data)
                imported_customers += 1
            
            # Check if vehicle exists
            vehicle = crud.get_vehicle_by_no_rangka(db, no_rangka=str(row['No Rangka']))
            
            if not vehicle:
                # Create vehicle
                tgl_beli = None
                if pd.notna(row.get('TGL BP')):
                    try:
                        tgl_beli = pd.to_datetime(row['TGL BP'])
                    except:
                        pass
                
                vehicle_data = schemas.VehicleCreate(
                    customer_id=customer.id,
                    no_rangka=str(row['No Rangka']),
                    no_polisi=str(row.get('NOPOL', '')) if pd.notna(row.get('NOPOL')) else None,
                    model=str(row['MODEL']),
                    type_mobil=str(row.get('TYPE MOBIL', '')) if pd.notna(row.get('TYPE MOBIL')) else None,
                    tgl_beli=tgl_beli,
                    cara_bayar=str(row.get('CARA BAYAR', '')) if pd.notna(row.get('CARA BAYAR')) else None,
                    grouping=str(row.get('Grouping', 'Regular')) if pd.notna(row.get('Grouping')) else 'Regular'
                )
                vehicle = crud.create_vehicle(db, vehicle=vehicle_data)
                imported_vehicles += 1
            
            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1} records...")
                
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            continue
    
    print(f"\nImport completed!")
    print(f"Imported {imported_customers} customers")
    print(f"Imported {imported_vehicles} vehicles")

def import_service_data(excel_path: str, db: Session):
    """
    Import service history data from Excel file
    """
    print(f"Reading service data from {excel_path}...")
    df = pd.read_excel(excel_path, sheet_name=0)
    
    print(f"Found {len(df)} records")
    
    imported_services = 0
    
    for idx, row in df.iterrows():
        try:
            # Find vehicle by no_rangka
            no_rangka = str(row.get('No Rangka', ''))
            if pd.isna(row.get('No Rangka')) or no_rangka == 'nan':
                continue
                
            vehicle = crud.get_vehicle_by_no_rangka(db, no_rangka=no_rangka)
            
            if not vehicle:
                continue
            
            # Parse service date
            service_date = None
            if pd.notna(row.get('Tgl')):
                try:
                    service_date = pd.to_datetime(row['Tgl'])
                except:
                    continue
            
            if not service_date:
                continue
            
            # Create service history
            service_data = schemas.ServiceHistoryCreate(
                vehicle_id=vehicle.id,
                no_invoice=str(row['No Invoice']),
                service_date=service_date,
                km=int(row.get('KM', 0)) if pd.notna(row.get('KM')) else 0,
                repair_type=str(row.get('Repair Type', '')) if pd.notna(row.get('Repair Type')) else None,
                labor=float(row.get('Labor', 0)) if pd.notna(row.get('Labor')) else 0,
                part=float(row.get('Part', 0)) if pd.notna(row.get('Part')) else 0,
                oli=float(row.get('Oli', 0)) if pd.notna(row.get('Oli')) else 0,
                total=float(row.get('Total', 0)) if pd.notna(row.get('Total')) else 0,
                sa_name=str(row.get('SA', '')) if pd.notna(row.get('SA')) else None
            )
            
            crud.create_service_history(db, service=service_data)
            imported_services += 1
            
            if (idx + 1) % 100 == 0:
                print(f"Processed {idx + 1} records...")
                
        except Exception as e:
            print(f"Error processing row {idx}: {e}")
            continue
    
    print(f"\nImport completed!")
    print(f"Imported {imported_services} service records")

def main():
    """
    Main import function
    """
    db = SessionLocal()
    
    try:
        # Import sales data
        sales_file = "data_input/sales_singleid_nik_final.xlsx"
        import_sales_data(sales_file, db)
        
        # Import service data
        service_file = "data_input/gs_singleid.xlsx"
        import_service_data(service_file, db)
        
    except Exception as e:
        print(f"Error during import: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
