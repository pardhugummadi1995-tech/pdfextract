from rise_engine.exporter import review_to_csv
from rise_engine.model import CategoryCounts, IndentLine, ProjectModel
from rise_engine.review import apply_review


def _model():
    return ProjectModel(
        source="x.pdf",
        material_indent=[
            IndentLine("HW-001", "Hettich Onsys 105° Hinges", "Hardware", 20, "Nos", ["Kitchen"], ["B1"], [9]),
            IndentLine(
                "HW-002",
                "Concealed Wall Brackets",
                "Hardware",
                None,
                None,
                ["Kitchen"],
                ["W1"],
                [9],
                flags=["Quantity Verification Required"],
            ),
        ],
        category_counts=CategoryCounts(1, 2, 2, 20, 0, 3, 1),
    )


def test_review_csv_has_approved_column_prefilled():
    csv_text = review_to_csv(_model())
    assert "Approved Qty" in csv_text.splitlines()[0]
    # Known qty is pre-filled; unknown left blank for the reviewer.
    assert ",20,Nos" in csv_text  # extracted + approved both 20


def test_apply_review_overrides_qty_and_clears_flags(tmp_path):
    model = _model()
    review = tmp_path / "review.csv"
    review.write_text(
        "SKU Code,Item Description,Category,Room(s),Cabinet(s),Extracted Qty,UOM,Source Page,Flags,Approved Qty,Reviewer Notes\n"
        "HW-001,Hettich Onsys 105° Hinges,Hardware,Kitchen,B1,20,Nos,9,,24,counted on site\n"
        "HW-002,Concealed Wall Brackets,Hardware,Kitchen,W1,,,9,Quantity Verification Required,4,\n"
    )
    apply_review(model, str(review))

    hinge = model.material_indent[0]
    assert hinge.total_qty == 24
    assert hinge.reviewed and hinge.review_notes == "counted on site"

    brackets = model.material_indent[1]
    assert brackets.total_qty == 4
    assert "Quantity Verification Required" not in brackets.flags  # resolved

    assert model.reviewed
    assert model.category_counts.hardware_qty == 28  # 24 + 4
