'''
This python file is a test library
Create and put information into a library that you have created
Pull information out of the library
'''

### Sample libraries ###

# This is a simple library consisting information on a 1:1 ratio #
test_catalog_1 = {'cat1':5,'cat2':2000,'cat3':10}

# print(f"\n{test_catalog_1   = }")

# another way to define a similar dictionary would be:

test_catalog_1_0 = {}           
test_catalog_1_0['cat1'] = 5
test_catalog_1_0['cat2'] = 2000
test_catalog_1_0['cat3'] = 10

# print(f"{test_catalog_1_0 = }")
# some of the most useful functions to interact with dictionaries:

# print(f"{test_catalog_1_0.keys() = } ")

# for k in test_catalog_1_0.keys():
#     print(f"{k =}")

# for v in test_catalog_1_0.values():
#     print(f"{v =}")
    
# for k,v in test_catalog_1_0.items():
#     print(f"{k =} {v =}")    
    
# test_catalog_1_0['cat1'] = 50

# for k,v in test_catalog_1_0.items():
#     print(f"{k =} {v =}")    

# Associate two pieces of information within one catalog
cat1={}
cat1['dataset1']={'status':'success', 'plan':'scan_x',  'scan_id':1, 'time': 'sometimestamp','uid':'ef29ee77a6257b789963c7c3'}
cat1['dataset2']={'status':'success', 'plan':'rel_scan','scan_id':2, 'time': 'sometimestamp','uid':'a5b495dbb0930e19d2a7fdfs'}
cat1['dataset3']={'status':'success', 'plan':'exafs',   'scan_id':10,'time': 'sometimestamp','uid':'cf8ee704e5e5d079c2aaa664'}

cat2={}
cat2['dataset1']={'status':'success', 'plan':'scan_y',  'scan_id':3, 'time': 'sometimestamp','uid':'815b703bba126ffea26b0b9d'}
cat2['dataset2']={'status':'success', 'plan':'ct',      'scan_id':4, 'time': 'sometimestamp','uid':'d8398d2c1129b553e0812689'}
cat2['dataset3']={'status':'aborted', 'plan':'xanes',   'scan_id':5, 'time': 'sometimestamp','uid':'5f03341a5f2563f73fab068c'}
cat2['dataset4']={'status':'aborted', 'plan':'scan_z',  'scan_id':6, 'time': 'sometimestamp','uid':'cf8ee704e5e5d079c2aaa664'}
cat2['dataset5']={'status':'success', 'plan':'exafs',   'scan_id':8, 'time': 'sometimestamp','uid':'4075b3e71529e20626c329df'}

cat3={}
cat3['dataset1']={'status':'success', 'plan':'scan_th', 'scan_id':1, 'time': 'sometimestamp','uid':'964c81960b5bd2434075b3es'}

test_catalog_2 = {'cat1':cat1,'cat2':cat2,'cat3':cat3}


# print('\n')
# print(f"{cat3 = }")
# print(f"Number of entries {len(cat3)}\n")

# print(f"{test_catalog_2 = }")
# print(f"Number of catalogs {len(test_catalog_2) = }")



# print(f"{test_catalog_2['cat2'] = }")
# print(f"Number of entries {len(test_catalog_2['cat2'])}\n")

# print(f"\n{test_catalog_2['cat3'] = }")
# print(f"Number of entries {len(test_catalog_2['cat3'])}\n")


# print(f"{test_catalog_2 = }")


# # three or more pieces of information within one catalog
# #test_catalog_3


# # how do I ask for a variable within the "catalog" variable
# # print(test_catalog_1['cat1'], test_catalog_1['cat2'], test_catalog_1['cat3'])
# # porblem is that it requres the user to know what the variable is. How do we allow it to 