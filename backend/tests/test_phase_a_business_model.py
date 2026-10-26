import pytest
import pytest_asyncio
import httpx

@pytest.mark.asyncio
async def test_business_presets_endpoint(client: httpx.AsyncClient):
    """
    Verify GET /api/v1/brands/presets and /api/v1/businesses/presets return
    the business presets (restaurant, retail, salon, clinic, supermarket, bakery).
    """
    for endpoint in ["/api/v1/brands/presets", "/api/v1/businesses/presets"]:
        res = await client.get(endpoint)
        assert res.status_code == 200, f"Failed for {endpoint}: {res.text}"
        data = res.json()
        assert "restaurant" in data
        assert "retail" in data
        assert "salon" in data
        assert "clinic" in data
        assert "supermarket" in data
        assert "bakery" in data

        # Check topics in restaurant preset
        rest = data["restaurant"]
        assert "default_topics" in rest
        assert "Food Quality & Taste" in rest["default_topics"]
        assert "Cleanliness & Hygiene" in rest["default_topics"]

@pytest.mark.asyncio
async def test_create_business_with_neutral_defaults_and_location(client: httpx.AsyncClient, user_factory):
    """
    Verify creating a business with a business_type creates neutral empty defaults
    (no fake competitors like ApexCloud), a default branch location, and topics from preset.
    """
    user = await user_factory(email="shopowner@gmail.com", role="brand_manager")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    payload = {
        "name": "Annapoorna Mess",
        "business_type": "restaurant",
        "industry": "Food & Beverage",
        "description": "Authentic local mess in T. Nagar"
    }

    res = await client.post("/api/v1/brands", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["name"] == "Annapoorna Mess"
    assert data["business_type"] == "restaurant"
    assert data["competitors"] == [], "Competitors must default to empty list, no fake enterprise competitors"
    assert "topics" in data and len(data["topics"]) > 0
    assert len(data["locations"]) == 1
    assert data["locations"][0]["name"] == "Main Branch"
    assert data["locations"][0]["is_primary"] is True

@pytest.mark.asyncio
async def test_location_crud_under_business(client: httpx.AsyncClient, user_factory):
    """
    Verify adding, updating, and deleting branch locations under a business.
    """
    user = await user_factory(email="multibranch@gmail.com", role="brand_manager")
    headers = {"Authorization": f"Bearer {user['access_token']}"}

    # 1. Create Business
    create_res = await client.post("/api/v1/brands", json={"name": "Sri Krishna Sweets", "business_type": "bakery"}, headers=headers)
    assert create_res.status_code == 200
    biz_id = create_res.json()["id"]

    # 2. Add New Branch
    new_loc_payload = {
        "name": "T. Nagar Branch",
        "city": "Chennai",
        "address": "12 Pondy Bazaar",
        "phone": "+91 98400 11223",
        "is_primary": False
    }
    add_loc_res = await client.post(f"/api/v1/brands/{biz_id}/locations", json=new_loc_payload, headers=headers)
    assert add_loc_res.status_code == 200
    biz_data = add_loc_res.json()
    assert len(biz_data["locations"]) == 2
    added_loc = next(loc for loc in biz_data["locations"] if loc["name"] == "T. Nagar Branch")
    assert added_loc["city"] == "Chennai"
    loc_id = added_loc["id"]

    # 3. Update Branch
    update_payload = {
        "name": "T. Nagar Mega Branch",
        "address": "12 Pondy Bazaar, Near Panagal Park",
        "is_primary": True
    }
    update_res = await client.put(f"/api/v1/brands/{biz_id}/locations/{loc_id}", json=update_payload, headers=headers)
    assert update_res.status_code == 200
    updated_locs = update_res.json()["locations"]
    target_loc = next(loc for loc in updated_locs if loc["id"] == loc_id)
    assert target_loc["name"] == "T. Nagar Mega Branch"
    assert target_loc["is_primary"] is True

    # 4. Delete Branch
    del_res = await client.delete(f"/api/v1/brands/{biz_id}/locations/{loc_id}", headers=headers)
    assert del_res.status_code == 200
    remaining_locs = del_res.json()["locations"]
    assert len(remaining_locs) == 1
    assert remaining_locs[0]["id"] != loc_id
