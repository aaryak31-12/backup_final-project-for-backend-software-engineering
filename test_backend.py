"""Basic tests using a separate temporary database (not your real data)."""

import os
import tempfile

from inventory_backend import InventoryManager


def run_tests():
    # Keep test data separate from the normal inventory.db file.
    temporary_folder = tempfile.TemporaryDirectory()
    test_file = os.path.join(temporary_folder.name, "test_inventory.db")

    try:
        inventory = InventoryManager(test_file)

        # 1. Add and retrieve a product.
        inventory.add_product("P001", "Notebook", "Stationery", 10, 5)
        assert inventory.get_product("P001")["quantity"] == 10

        # 2. Add another product and check total count.
        inventory.add_product("P002", "Apple", "Food", 2, 3)
        assert len(inventory.get_all_products()) == 2

        # 3. Duplicate IDs must cause an error (also ignores case).
        try:
            inventory.add_product("p001", "Other", "Food", 1, 0)
            raise AssertionError("Duplicate ID was allowed")
        except ValueError:
            pass

        # 4. Edit a product without changing its ID.
        inventory.edit_product("P001", name="Large Notebook", quantity=7)
        assert inventory.get_product("P001")["name"] == "Large Notebook"
        assert inventory.get_product("P001")["product_id"] == "P001"

        # 5. Receive and sell stock.
        inventory.increase_stock("P001", 3)
        inventory.decrease_stock("P001", 2)
        assert inventory.get_product("P001")["quantity"] == 8

        # 6. Reject selling more units than exist.
        try:
            inventory.decrease_stock("P001", 999)
            raise AssertionError("Negative inventory was allowed")
        except ValueError:
            pass
        assert inventory.get_product("P001")["quantity"] == 8

        # 7. Reject negative or fractional quantities.
        try:
            inventory.edit_product("P001", quantity="-1")
            raise AssertionError("Negative input was allowed")
        except ValueError:
            pass

        # 8. Search and category filter.
        assert len(inventory.search_products("large")) == 1
        assert len(inventory.filter_products("food")) == 1

        # 9. Low stock: Apple has 2 units and a threshold of 3.
        assert len(inventory.get_low_stock_products()) == 1
        inventory.increase_stock("P002", 3)
        assert len(inventory.get_low_stock_products()) == 0

        # 10. Dashboard numbers come from the saved products.
        stats = inventory.get_dashboard_stats()
        assert stats["total_products"] == 2
        assert stats["total_inventory_quantity"] == 13
        assert stats["low_stock_products"] == 0

        # 11. Deleting a product with stock must fail.
        try:
            inventory.remove_product("P002")
            raise AssertionError("Product with stock was deleted")
        except ValueError:
            pass

        # 12. Product can be deleted after stock reaches zero.
        inventory.decrease_stock("P002", 5)
        assert inventory.remove_product("P002") is True
        assert inventory.get_product("P002") is None

        # 13. Reopening the database should keep saved information.
        reopened = InventoryManager(test_file)
        assert reopened.get_product("P001")["quantity"] == 8
        assert reopened.get_product("P002") is None

        print("All 13 backend checks passed!")

    finally:
        temporary_folder.cleanup()


if __name__ == "__main__":
    run_tests()