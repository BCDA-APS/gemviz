from test_infomation_database import test_catalog_2

def test_function():
    return (test_catalog_2)


tf = test_function()

thekeyfromthepulldownmenu='cat2'
selected_catalog=tf[thekeyfromthepulldownmenu]

print('\n\nPrint all the available "runs" from the selected catalog:\n')

for k in selected_catalog.keys():
    print(f"{k = }")

print('\n\nPrint all the content of each of those "runs":\n')

for k in selected_catalog.keys():
    dataset_content=selected_catalog[k]
    print(f"{k} = {dataset_content}")
    
    
for k in selected_catalog.keys():
    dataset_content=selected_catalog[k]
    scan_ids=dataset_content['scan_id']   
    print(f"{k} - scan_id = {scan_ids}")
    
#or in a more concise fashion - gives the exact same result as above:
for k in selected_catalog.keys():
    scan_ids=selected_catalog[k]['scan_id']   
    print(f"{k} - scan_id = {scan_ids}")



scan_id_list_1=[]
for k in selected_catalog.keys():
    scan_id_list_1.append(selected_catalog[k]['scan_id'])

print(f"{scan_id_list_1 = }")



    
# try comprehension list:
scan_id_list_2=[str(selected_catalog[k]['scan_id']) for k in selected_catalog.keys()]

# this is basically the same as creating a list with a for loop, just reshuffled a bit.



print(f"{scan_id_list_2 = }")

# for i in scan_id_list_2:   #this is how you would stick the scan_id into the dropdown menu
#     print(f"{i}")
    