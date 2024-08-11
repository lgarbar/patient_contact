import pandas as pd
import numpy as np
from datetime import datetime, timedelta 
import argparse
import tkinter as tk
from tkinter import ttk
import os
import subprocess  # Import subprocess module

# Activate mamba environment
# subprocess.run(["mamba", "activate", "mne"], shell=True)

patients_to_contact = '/Users/danielgarcia-barnett/Desktop/patient_data/patient_data.csv'
contacted_patients_fpath = '/Users/danielgarcia-barnett/Desktop/patient_data/contacted_patients.csv'

def pop_df_row(ind, df_to_remove, df_to_add):
    cols = ['Ind', 'ptp_num', 'last_visit_date', 'phone_number', 'email']
    # Ensure the columns exist in the DataFrame
    df_to_remove = df_to_remove.reindex(columns=cols, fill_value=np.nan)
    df_to_add = df_to_add.reindex(columns=cols, fill_value=np.nan)

    # "Pop" the row at index ind from df_to_remove
    row_to_move = df_to_remove.loc[[ind]]

    # Remove the row from df_to_remove
    df_to_remove = df_to_remove.drop(index=ind).reset_index(drop=True)

    # Append the row to df_to_add
    df_to_add = pd.concat([df_to_add, row_to_move]).reset_index(drop=True)

    return df_to_remove[cols], df_to_add.sort_values(by='Ind', ascending=True).reset_index(drop=True)[cols]

def filt_data(data_fpath):
    data_df = pd.read_csv(data_fpath, index_col=0) 
    data_df['last_visit_date'] = pd.to_datetime(data_df['last_visit_date'])

    # Add 'Ind' column to maintain original order
    data_df['Ind'] = data_df.index

    # Calculate the cutoff date for 6 months ago
    today = datetime.now()
    six_months_ago = today - timedelta(days=6*30)  # Approximate 6 months as 180 days

    # Load contacted patients data
    if (os.path.exists(contacted_patients_fpath)):
        contacted_patients_df = pd.read_csv(contacted_patients_fpath, index_col=0)
    else:
        contacted_patients_df = pd.DataFrame(columns=data_df.columns)

    # Filter out patients already contacted
    filtered_df = data_df[(data_df['last_visit_date'] <= six_months_ago) & (~data_df['ptp_num'].isin(contacted_patients_df['ptp_num']))]
    filtered_df.to_csv(patients_to_contact)
    return filtered_df

def display_dataframe(df):
    root = tk.Tk()
    root.title("Filtered Dataframe")
    
    # Add 'Ind' column to maintain original order
    df['Ind'] = df.index
    
    # Exclude 'Ind' column from display
    display_columns = [col for col in df.columns if col != 'Ind']
    
    # Display the dataframe using tkinter with checkboxes
    tree = ttk.Treeview(root)
    tree["columns"] = display_columns
    tree["show"] = "headings"
    
    for col in display_columns:
        tree.heading(col, text=col)
    
    for index, row in df.iterrows():
        values = [row[col] for col in display_columns]
        tree.insert("", "end", values=values, iid=index)  # Use iid to store the DataFrame index
    
    def on_double_click(event):
        item = tree.identify_row(event.y)
        if item:
            # Get the row data
            row_data = tree.item(item, "values")
            ptp_num = int(row_data[display_columns.index('ptp_num')])  # Get 'ptp_num' value

            # Load dataframes
            data_df = pd.read_csv(patients_to_contact, index_col=0)
            contacted_patients_df = pd.read_csv(contacted_patients_fpath, index_col=0) if os.path.exists(contacted_patients_fpath) else pd.DataFrame(columns=df.columns)

            if "grayed" in tree.item(item, "tags"):
                # If already grayed, revert to default color and move back to patients_to_contact
                print(f'Moving {ptp_num} back to original csv')
                if ptp_num in contacted_patients_df['ptp_num'].values:
                    row_index = contacted_patients_df.index[contacted_patients_df['ptp_num'] == ptp_num].tolist()[0]
                    contacted_patients_df, data_df = pop_df_row(row_index, contacted_patients_df, data_df)
                    print(f'Moved {ptp_num}')
                else:
                    print(f'Error: ptp_num {ptp_num} not found in contacted_patients_df')
                tree.item(item, tags=("",))
            else:
                # Move from patients_to_contact to contacted_patients
                if ptp_num in data_df['ptp_num'].values:
                    row_index = data_df.index[data_df['ptp_num'] == ptp_num].tolist()[0]
                    data_df, contacted_patients_df = pop_df_row(row_index, data_df, contacted_patients_df)
                else:
                    print(f'Error: ptp_num {ptp_num} not found in data_df')
                tree.item(item, tags=("grayed",))
                tree.tag_configure("grayed", background="lightgrey")
            
            # Save updated dataframes
            data_df.to_csv(patients_to_contact)
            contacted_patients_df.to_csv(contacted_patients_fpath)

    def on_click(event):
        item = tree.identify_row(event.y)
        if item:
            # Reset the color of previously clicked row
            if tree.clicked_item and tree.clicked_item != item and "grayed" not in tree.item(tree.clicked_item, "tags"):
                tree.item(tree.clicked_item, tags=("",))
            # Set the color of the clicked row to dark blue
            if "grayed" not in tree.item(item, "tags"):
                tree.item(item, tags=("clicked",))
                tree.tag_configure("clicked", background="darkblue")
                tree.clicked_item = item

    def on_enter(event):
        item = tree.identify_row(event.y)
        if item and item != tree.prev_item:
            if tree.prev_item and "clicked" not in tree.item(tree.prev_item, "tags") and "grayed" not in tree.item(tree.prev_item, "tags"):
                tree.item(tree.prev_item, tags=("",))
            if "clicked" not in tree.item(item, "tags") and "grayed" not in tree.item(item, "tags"):
                tree.item(item, tags=("blue",))
                tree.tag_configure("blue", background="lightblue")
            tree.prev_item = item

    def on_leave(event):
        if tree.prev_item:
            if "clicked" not in tree.item(tree.prev_item, "tags") and "grayed" not in tree.item(tree.prev_item, "tags"):
                tree.item(tree.prev_item, tags=("",))
            tree.prev_item = None

    # Bind the events
    tree.bind("<Button-1>", on_click)
    tree.bind("<Double-1>", on_double_click)
    tree.bind("<Motion>", on_enter)
    tree.bind("<Leave>", on_leave)

    # Initialize previous item and clicked item trackers
    tree.prev_item = None
    tree.clicked_item = None
    
    tree.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", help="File path to the data")
    args = parser.parse_args()

    if args.file:
        data_fpath = args.file
    else:
        data_fpath = '/Users/danielgarcia-barnett/Desktop/Coding/dentist_upgrade/patient_contact_summary/patient_contact/patient_contact/test_data.csv'

    filtered_data = filt_data(data_fpath)
    filtered_data['Ind'] = filtered_data.index  # Add 'Ind' column to maintain original order
    display_dataframe(filtered_data)