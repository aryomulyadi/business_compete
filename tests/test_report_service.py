from deep_research_team.backend.report_service import get_brand_concepts, get_brand_names


class TestGetBrandNames:
    def test_empty_report(self):
        assert get_brand_names("") == []

    def test_no_brand_section(self):
        assert get_brand_names("# Laporan\nBla bla") == []

    def test_bold_bullet_format(self):
        report = "## 8. Brand Strategy\n- **Warung Sejahtera**: desc\n- **TechMart**: desc"
        assert get_brand_names(report) == ["Warung Sejahtera", "TechMart"]

    def test_bold_asterisk_format(self):
        report = "## 8. Brand Strategy\n* **Warung Sejahtera**: desc\n* **TechMart**: desc"
        assert get_brand_names(report) == ["Warung Sejahtera", "TechMart"]

    def test_numbered_bold_format(self):
        report = "## Brand Strategy\n1. **Warung Sejahtera**: desc\n2. **TechMart**: desc"
        assert get_brand_names(report) == ["Warung Sejahtera", "TechMart"]

    def test_no_bold_format(self):
        report = "## Brand Strategy & Naming\n- Warung Sejahtera: desc\n- TechMart: desc"
        assert get_brand_names(report) == ["Warung Sejahtera", "TechMart"]

    def test_numbered_no_bold_format(self):
        report = "## 8. Brand Strategy\n1. Warung Sejahtera: desc\n2. TechMart: desc"
        assert get_brand_names(report) == ["Warung Sejahtera", "TechMart"]

    def test_skip_instructional_lines(self):
        report = (
            "## 8. Brand Strategy\n"
            "- Opsi nama brand strategis (dengan makna, filosofi)\n"
            "- **Warung Sejahtera**: desc\n"
        )
        assert get_brand_names(report) == ["Warung Sejahtera"]

    def test_mixed_formats(self):
        report = (
            "## 8. Brand Strategy\n"
            "- **BoldBrand**: desc\n"
            "1. NumberedBrand: desc\n"
            "- PlainBrand: desc\n"
            "## 9. Other Section\n"
        )
        names = get_brand_names(report)
        assert "BoldBrand" in names, f"got {names}"
        assert "NumberedBrand" in names, f"got {names}"
        assert "PlainBrand" in names, f"got {names}"


class TestGetBrandNamesRealReports:
    def test_heading_bold_opsi_format(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "\n"
            "### Strategi Positioning\n"
            "*   **Differentiation:** some text\n"
            "*   **Target Audience:** some text\n"
            "\n"
            "### Opsi Nama Brand Strategis\n"
            "\n"
            "#### Opsi 1: **SASTRA AROMA**\n"
            "*   **Makna Literal:** arti\n"
            "*   **Filosofi:** nilai\n"
            "*   **Target Pasar:** anak muda\n"
            "*   **Positioning:** premium\n"
            "\n"
            "#### Opsi 2: **VOLAR**\n"
            "*   **Makna Literal:** arti dua\n"
            "*   **Filosofi:** nilai dua\n"
            "## 9. Strategi Positioning\n"
        )
        names = get_brand_names(report)
        assert names == ["SASTRA AROMA", "VOLAR"], f"got {names}"

    def test_heading_quoted_opsi_format(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "### Opsi nama brand strategis\n"
            "#### Opsi 1: \"HIJAB COCO\"\n"
            "details\n"
            "#### Opsi 2: \"SEDAIAH\"\n"
            "details\n"
            "## 9. Other\n"
        )
        names = get_brand_names(report)
        assert names == ["HIJAB COCO", "SEDAIAH"], f"got {names}"

    def test_bold_opsi_format(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "**Opsi 1: Padu Pakaian**\n"
            "- **Makna Literal:** arti\n"
            "**Opsi 2: Jelas Label**\n"
            "- **Makna Literal:** arti\n"
            "## 9. Other\n"
        )
        names = get_brand_names(report)
        assert names == ["Padu Pakaian", "Jelas Label"], f"got {names}"

    def test_heading_plain_opsi_format(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "### Opsi 1: KOKOH\n"
            "* Makna: arti\n"
            "### Opsi 2: ARUNA H2O\n"
            "* Makna: arti\n"
            "## 9. Other\n"
        )
        names = get_brand_names(report)
        assert names == ["KOKOH", "ARUNA H2O"], f"got {names}"

    def test_bold_numbered_format(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "**1. NusaSip**\n"
            "- Makna: arti\n"
            "**2. RantaiHijau**\n"
            "- Makna: arti\n"
            "## 9. Other\n"
        )
        names = get_brand_names(report)
        assert names == ["NusaSip", "RantaiHijau"], f"got {names}"


class TestGetBrandConcepts:
    def test_empty(self):
        assert get_brand_concepts("") == []

    def test_no_section(self):
        assert get_brand_concepts("# Report") == []

    def test_bold_format_with_fields(self):
        report = (
            "## 8. Brand Strategy\n"
            "- **Warung Sejahtera**: \n"
            "  Makna: Sejahtera berarti makmur\n"
            "  Filosofi: Kekeluargaan\n"
            "  Target Pasar: Keluarga muda\n"
            "  Positioning: Premium\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) == 1
        assert concepts[0].name == "Warung Sejahtera"
        assert "makmur" in concepts[0].meaning
        assert concepts[0].philosophy == "Kekeluargaan"
        assert concepts[0].target_market == "Keluarga muda"
        assert concepts[0].positioning == "Premium"

    def test_case_insensitive_field_labels(self):
        report = (
            "## BRAND STRATEGY\n"
            "- **Brand A**: \n"
            "  makna kata: arti\n"
            "  filosofi: nilai\n"
            "  target audience: anak muda\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) == 1
        assert concepts[0].name == "Brand A"
        assert concepts[0].meaning == "arti"
        assert "nilai" in concepts[0].philosophy

    def test_numbered_format(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "1. **Warung Sejahtera**:\n"
            "   Makna: Makmur dan sejahtera\n"
            "   Filosofi: Kebersamaan\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) == 1
        assert "Makmur" in concepts[0].meaning

    def test_no_bold_format(self):
        report = (
            "## Brand Strategy\n"
            "- Warung Sejahtera:\n"
            "  Makna: Makmur\n"
            "  Filosofi: Kekeluargaan\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) >= 1
        assert concepts[0].name == "Warung Sejahtera"


class TestGetBrandConceptsRealReports:
    def test_heading_bold_opsi_with_fields(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "### Opsi Nama Brand Strategis\n"
            "#### Opsi 1: **SASTRA AROMA**\n"
            "*   **Makna Literal:** Sastra (Seni) + Aroma\n"
            "*   **Filosofi:** Setiap parfum adalah puisi\n"
            "*   **Target Pasar:** Pecinta seni\n"
            "*   **Positioning:** Storytelling\n"
            "#### Opsi 2: **VOLAR**\n"
            "*   **Makna Literal:** Volare (terbang)\n"
            "*   **Filosofi:** Kebebasan\n"
            "## 9. Other\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) == 2, f"got {len(concepts)}"
        assert concepts[0].name == "SASTRA AROMA"
        assert "Sastra" in concepts[0].meaning
        assert concepts[0].philosophy == "Setiap parfum adalah puisi"
        assert concepts[0].target_market == "Pecinta seni"
        assert concepts[1].name == "VOLAR"

    def test_bold_opsi_with_fields(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "**Opsi 1: Padu Pakaian**\n"
            "- **Makna Literal:** Padu (paduan) + Pakaian\n"
            "- **Filosofi:** Harmoni dalam busana\n"
            "- **Target Pasar:** Pria dewasa\n"
            "- **Positioning:** Elegan\n"
            "**Opsi 2: Jelas Label**\n"
            "- **Makna Literal:** Jelas + Label\n"
            "## 9. Other\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) == 2, f"got {len(concepts)}"
        assert concepts[0].name == "Padu Pakaian"
        assert "Harmoni" in concepts[0].philosophy
        assert concepts[0].positioning == "Elegan"
        assert concepts[1].name == "Jelas Label"

    def test_heading_plain_opsi_format(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "### Opsi 1: KOKOH\n"
            "*   **Makna & Filosofi:** Kuat dan tahan lama\n"
            "*   **Target Pasar:** Pria\n"
            "### Opsi 2: ARUNA H2O\n"
            "*   **Makna & Filosofi:** Air kehidupan\n"
            "## 9. Other\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) == 2, f"got {len(concepts)}"
        assert concepts[0].name == "KOKOH"
        assert "Kuat" in concepts[0].meaning
        assert concepts[1].name == "ARUNA H2O"

    def test_bold_numbered_with_quoted_fields(self):
        report = (
            "## 8. Brand Strategy & Naming\n"
            "**1. NusaSip**\n"
            "- **Makna:** Nusa (Nusantara) + Sip (teguk)\n"
            "- **Filosofi:** Kebanggaan lokal\n"
            "- **Target Pasar:** Anak muda\n"
            "**2. RantaiHijau**\n"
            "- **Makna:** Rantai + Hijau\n"
            "## 9. Other\n"
        )
        concepts = get_brand_concepts(report)
        assert len(concepts) == 2, f"got {len(concepts)}"
        assert concepts[0].name == "NusaSip"
        assert "Nusantara" in concepts[0].meaning
        assert concepts[1].name == "RantaiHijau"
