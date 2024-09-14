import asyncio
from typing import List
from msgraph import GraphServiceClient
from msgraph.generated.drives.item.items.item.children.children_request_builder import ChildrenRequestBuilder
from msgraph.generated.users.users_request_builder import UsersRequestBuilder
from msgraph.generated.models.user import User
from msgraph.generated.models.o_data_errors.o_data_error import ODataError
from kiota_abstractions.base_request_configuration import RequestConfiguration
from azure.identity import ClientSecretCredential

tenant_id = '<tenant_id>'
client_id = '<client_id>'
client_secret = '<client_secret>'

scopes = ['https://graph.microsoft.com/.default']

credential = ClientSecretCredential(tenant_id, client_id, client_secret)
graph_client = GraphServiceClient(credential, scopes)

# get child items count
async def get_child_items_count(drive_id: str, drive_item_id: str) -> int:
    items_count = 0
    all_drive_item_folders_ids: List[str] = []
    # return only id, name and folder
    query_params = ChildrenRequestBuilder.ChildrenRequestBuilderGetQueryParameters(
        select = ["id","name","folder"],
    )

    request_configuration = RequestConfiguration(
        query_parameters = query_params,
    )
    # process first page
    drive_items_response = await graph_client.drives.by_drive_id(drive_id).items.by_drive_item_id(drive_item_id).children.get(request_configuration = request_configuration)
    if drive_items_response:
        items_count+=len(drive_items_response.value)
        for i in range(len(drive_items_response.value)):
            child_item = drive_items_response.value[i]
            #print(f"id: {child_item.id}, name: {child_item.name}")
            if child_item.folder is not None and child_item.folder.child_count > 0:
                all_drive_item_folders_ids.append(child_item.id)
    
    # process other pages
    while drive_items_response is not None and drive_items_response.odata_next_link is not None:
        drive_items_response = await graph_client.drives.by_drive_id(drive_id).items.by_drive_item_id(drive_item_id).children.with_url(drive_items_response.odata_next_link).get(request_configuration = request_configuration)
        if drive_items_response:
            items_count+=len(drive_items_response.value)
            for i in range(len(drive_items_response.value)):
                child_item = drive_items_response.value[i]
                #print(f"id: {child_item.id}, name: {child_item.name}")
                if child_item.folder is not None and child_item.folder.child_count > 0:
                    all_drive_item_folders_ids.append(child_item.id)

    for i in range(len(all_drive_item_folders_ids)):
        items_count += await get_child_items_count(drive_id, all_drive_item_folders_ids[i])
    return items_count

# get all users except guest users
async def get_all_users() -> List[User]:
    users: List[User] = []
    query_params = UsersRequestBuilder.UsersRequestBuilderGetQueryParameters(
        select = ["id","userPrincipalName"],
        filter = "userType eq 'member'"
    )
    request_configuration = RequestConfiguration(
        query_parameters = query_params,
    )
    users_response = await graph_client.users.get(request_configuration)
    if users_response:
        for i in range(len(users_response.value)):
            users.append(users_response.value[i])

    while users_response is not None and users_response.odata_next_link is not None:
        users_response = await graph_client.users.with_url(users_response.odata_next_link).get(request_configuration)
        if users_response:
            for i in range(len(users_response.value)):
                users.append(users_response.value[i])

    return users

# main function
async def get_users_drives_files_count():
    users = await get_all_users()
    if users:
        for i in range(len(users)):
            user = users[i]
            try:
                drives = await graph_client.users.by_user_id(user.id).drives.get()
                if drives:
                    for i in range(len(drives.value)):
                        drive = drives.value[i]
                        items_count = await get_child_items_count(drive.id, 'root')
                        print(f"{user.user_principal_name}: drive '{drive.name}' has {items_count} item(s)")
            except ODataError as e:
                print(f"Failed for user {user.user_principal_name} ({user.id}). {e.primary_message}")

asyncio.run(get_users_drives_files_count())