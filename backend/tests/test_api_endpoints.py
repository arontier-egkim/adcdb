"""Integration tests for all API endpoints using httpx AsyncClient."""

import pytest


class TestHealthEndpoint:
    """Tests for GET /api/v1/health."""

    @pytest.mark.asyncio
    async def test_health_returns_ok(self, client):
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestADCEndpoints:
    """Tests for /api/v1/adcs endpoints."""

    @pytest.mark.asyncio
    async def test_list_adcs_empty(self, client):
        """Empty DB should return empty list."""
        resp = await client.get("/api/v1/adcs")
        assert resp.status_code == 200
        assert resp.json() == []

    @pytest.mark.asyncio
    async def test_list_adcs_with_data(self, client, seed_data):
        """Should return ADCListItem records with flat component names."""
        resp = await client.get("/api/v1/adcs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # Check first item has flat fields
        names = [d["name"] for d in data]
        assert "Trastuzumab deruxtecan" in names
        # Check flat fields exist on first item
        item = next(d for d in data if d["name"] == "Trastuzumab deruxtecan")
        assert item["antibody_name"] == "Trastuzumab"
        assert item["antigen_name"] == "HER2"
        assert item["linker_name"] == "MC-VC-PABC"
        assert item["payload_name"] == "MMAE"
        assert item["status"] == "approved"

    @pytest.mark.asyncio
    async def test_list_adcs_filter_by_status(self, client, seed_data):
        """Status filter should return only matching ADCs."""
        resp = await client.get("/api/v1/adcs?status=approved")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert all(d["status"] == "approved" for d in data)

    @pytest.mark.asyncio
    async def test_list_adcs_filter_by_name(self, client, seed_data):
        """Name filter with q param should use LIKE matching."""
        resp = await client.get("/api/v1/adcs?q=Trastuzumab")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "Trastuzumab deruxtecan"

    @pytest.mark.asyncio
    async def test_list_adcs_filter_by_antigen(self, client, seed_data):
        """Antigen filter should match exact antigen name."""
        resp = await client.get("/api/v1/adcs?antigen=HER2")
        assert resp.status_code == 200
        data = resp.json()
        assert all(d["antigen_name"] == "HER2" for d in data)

    @pytest.mark.asyncio
    async def test_list_adcs_pagination(self, client, seed_data):
        """Pagination should limit results."""
        resp = await client.get("/api/v1/adcs?per_page=1")
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    @pytest.mark.asyncio
    async def test_list_adcs_invalid_page(self, client):
        """Page < 1 should return 422 validation error."""
        resp = await client.get("/api/v1/adcs?page=0")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_adcs_per_page_too_large(self, client):
        """per_page > 100 should return 422 validation error."""
        resp = await client.get("/api/v1/adcs?per_page=200")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_get_adc_detail(self, client, seed_data):
        """Should return full ADCRead with nested components and activities."""
        adc_id = seed_data["adc_id"]
        resp = await client.get(f"/api/v1/adcs/{adc_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Trastuzumab deruxtecan"
        assert data["brand_name"] == "Enhertu"
        # Nested antibody
        assert data["antibody"]["name"] == "Trastuzumab"
        # Nested antigen (via antibody)
        assert data["antibody"]["antigen"]["name"] == "HER2"
        # Nested linker
        assert data["linker"]["name"] == "MC-VC-PABC"
        # Nested payload
        assert data["payload"]["name"] == "MMAE"
        # Activities
        assert len(data["activities"]) == 1
        assert data["activities"][0]["nct_number"] == "NCT03248492"

    @pytest.mark.asyncio
    async def test_get_adc_not_found(self, client):
        """Invalid ADC ID should return 404."""
        resp = await client.get("/api/v1/adcs/nonexistent-uuid")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "ADC not found"

    @pytest.mark.asyncio
    async def test_get_adc_structure_no_structure(self, client, seed_data):
        """ADC without structure_3d_path should return 404."""
        adc_id = seed_data["adc_id2"]  # No structure
        resp = await client.get(f"/api/v1/adcs/{adc_id}/structure")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_adc_structure_not_found(self, client):
        """Nonexistent ADC structure request should return 404."""
        resp = await client.get("/api/v1/adcs/nonexistent-uuid/structure")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "ADC not found"

    @pytest.mark.asyncio
    async def test_create_adc(self, client, seed_data):
        """POST should create a new ADC and return ADCRead."""
        body = {
            "name": "New Test ADC",
            "status": "investigative",
            "antibody_id": seed_data["antibody_id"],
            "linker_id": seed_data["linker_id"],
            "payload_id": seed_data["payload_id"],
        }
        resp = await client.post("/api/v1/adcs", json=body)
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "New Test ADC"
        assert data["antibody"]["name"] == "Trastuzumab"


class TestAntibodyEndpoints:
    """Tests for /api/v1/antibodies endpoints."""

    @pytest.mark.asyncio
    async def test_list_antibodies(self, client, seed_data):
        """Should return antibodies with nested antigen."""
        resp = await client.get("/api/v1/antibodies")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Check nested antigen
        t = next(d for d in data if d["name"] == "Trastuzumab")
        assert t["antigen"]["name"] == "HER2"

    @pytest.mark.asyncio
    async def test_get_antibody_detail(self, client, seed_data):
        """Should return single antibody with nested antigen."""
        ab_id = seed_data["antibody_id"]
        resp = await client.get(f"/api/v1/antibodies/{ab_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Trastuzumab"
        assert data["antigen"]["name"] == "HER2"
        assert data["heavy_chain_seq"] is not None

    @pytest.mark.asyncio
    async def test_get_antibody_not_found(self, client):
        """Invalid antibody ID should return 404."""
        resp = await client.get("/api/v1/antibodies/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_antibody_adcs(self, client, seed_data):
        """Should return linked ADCs as ADCListItem."""
        ab_id = seed_data["antibody_id"]
        resp = await client.get(f"/api/v1/antibodies/{ab_id}/adcs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all("antibody_name" in d for d in data)


class TestAntigenEndpoints:
    """Tests for /api/v1/antigens endpoints."""

    @pytest.mark.asyncio
    async def test_list_antigens(self, client, seed_data):
        """Should return antigens."""
        resp = await client.get("/api/v1/antigens")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    @pytest.mark.asyncio
    async def test_get_antigen_detail(self, client, seed_data):
        """Should return single antigen."""
        ag_id = seed_data["antigen_id"]
        resp = await client.get(f"/api/v1/antigens/{ag_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "HER2"

    @pytest.mark.asyncio
    async def test_get_antigen_not_found(self, client):
        resp = await client.get("/api/v1/antigens/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_antigen_adcs(self, client, seed_data):
        """Should return ADCs targeting this antigen (2-hop: Antigen <- Antibody <- ADC)."""
        ag_id = seed_data["antigen_id"]
        resp = await client.get(f"/api/v1/antigens/{ag_id}/adcs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        assert all(d["antigen_name"] == "HER2" for d in data)


class TestLinkerEndpoints:
    """Tests for /api/v1/linkers endpoints."""

    @pytest.mark.asyncio
    async def test_list_linkers(self, client, seed_data):
        resp = await client.get("/api/v1/linkers")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["name"] == "MC-VC-PABC"

    @pytest.mark.asyncio
    async def test_get_linker_detail(self, client, seed_data):
        lk_id = seed_data["linker_id"]
        resp = await client.get(f"/api/v1/linkers/{lk_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["cleavable"] is True
        assert data["smiles"] is not None

    @pytest.mark.asyncio
    async def test_get_linker_not_found(self, client):
        resp = await client.get("/api/v1/linkers/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_linker_adcs(self, client, seed_data):
        lk_id = seed_data["linker_id"]
        resp = await client.get(f"/api/v1/linkers/{lk_id}/adcs")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestPayloadEndpoints:
    """Tests for /api/v1/payloads endpoints."""

    @pytest.mark.asyncio
    async def test_list_payloads(self, client, seed_data):
        resp = await client.get("/api/v1/payloads")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_get_payload_detail(self, client, seed_data):
        pl_id = seed_data["payload_id"]
        resp = await client.get(f"/api/v1/payloads/{pl_id}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "MMAE"

    @pytest.mark.asyncio
    async def test_get_payload_not_found(self, client):
        resp = await client.get("/api/v1/payloads/nonexistent")
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_get_payload_adcs(self, client, seed_data):
        pl_id = seed_data["payload_id"]
        resp = await client.get(f"/api/v1/payloads/{pl_id}/adcs")
        assert resp.status_code == 200
        assert len(resp.json()) >= 1


class TestSearchEndpoints:
    """Tests for /api/v1/search endpoints."""

    @pytest.mark.asyncio
    async def test_unified_search(self, client, seed_data):
        """Text search should return results grouped by entity type."""
        resp = await client.get("/api/v1/search?q=Trastuzumab")
        assert resp.status_code == 200
        data = resp.json()
        assert "adcs" in data
        assert "antibodies" in data
        assert "antigens" in data
        assert "linkers" in data
        assert "payloads" in data
        # Should find the ADC and antibody
        assert len(data["adcs"]) >= 1
        assert len(data["antibodies"]) >= 1

    @pytest.mark.asyncio
    async def test_unified_search_antigen_matches_gene_name(self, client, seed_data):
        """Antigen search should match gene_name via OR."""
        resp = await client.get("/api/v1/search?q=ERBB2")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["antigens"]) >= 1
        assert data["antigens"][0]["gene_name"] == "ERBB2"

    @pytest.mark.asyncio
    async def test_unified_search_no_results(self, client, seed_data):
        """Search with non-matching term should return empty arrays."""
        resp = await client.get("/api/v1/search?q=zzzznonexistent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["adcs"] == []
        assert data["antibodies"] == []

    @pytest.mark.asyncio
    async def test_unified_search_requires_q(self, client):
        """Missing q parameter should return 422."""
        resp = await client.get("/api/v1/search")
        assert resp.status_code == 422


class TestStatsEndpoint:
    """Tests for GET /api/v1/stats."""

    @pytest.mark.asyncio
    async def test_stats_with_data(self, client, seed_data):
        """Stats should return aggregated counts."""
        resp = await client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_adcs"] == 3
        assert isinstance(data["top_antigens"], list)
        assert isinstance(data["top_payload_targets"], list)
        # Pipeline should have all 5 keys
        pipeline = data["pipeline"]
        for key in ["approved", "phase_3", "phase_2", "phase_1", "investigative"]:
            assert key in pipeline
        assert pipeline["approved"] == 2

    @pytest.mark.asyncio
    async def test_stats_empty_db(self, client):
        """Stats on empty DB should return zeros."""
        resp = await client.get("/api/v1/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_adcs"] == 0
        pipeline = data["pipeline"]
        assert all(v == 0 for v in pipeline.values())
