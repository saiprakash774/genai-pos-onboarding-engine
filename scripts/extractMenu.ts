import * as fs from 'fs';
import * as path from 'path';

// Note: To read excel in TS we would use a library like 'xlsx'. 
// For this regeneration proof, we mock the core logic that the Gherkin spec enforces:
// 1. Forward Fill missing parent data
// 2. Map modifiers based on category

interface MenuItem {
    Base_Drink: string | null;
    Size: string | null;
    Category: string | null;
    Base_Price: number | null;
}

function mapModifiers(category: string): string[] {
    const allowedModifiers: string[] = [];
    if (category === "Cold Coffee") {
        allowedModifiers.push("Cold Foam");
    }
    if (category === "Hot Coffee" || category === "Frappuccino") {
        allowedModifiers.push("Whipped Cream");
    }
    return allowedModifiers;
}

function parseMenu(rows: any[]) {
    // 1. Forward-fill logic
    let currentBaseDrink = "";
    let currentCategory = "";

    const parsedMenu = [];

    for (const row of rows) {
        if (!row.Base_Drink && !row.Size && !row.Category && !row.Base_Price) {
            continue; // drop completely empty rows
        }

        if (row.Base_Drink) currentBaseDrink = row.Base_Drink;
        if (row.Category) currentCategory = row.Category;

        const size = row.Size || "";
        const basePrice = row.Base_Price !== undefined ? row.Base_Price : 0.0;

        const allowedModifiers = mapModifiers(currentCategory);

        parsedMenu.push({
            Base_Drink: currentBaseDrink,
            Category: currentCategory,
            Size: size,
            Base_Price: basePrice,
            Allowed_Modifiers: allowedModifiers
        });
    }

    return parsedMenu;
}

function main() {
    console.log("Regenerated Parsing Agent Logic in TypeScript");
    // Mocking the input that would normally come from Excel
    const mockInput = [
        { Base_Drink: "Caffe Americano", Size: "Tall", Category: "Hot Coffee", Base_Price: 3.25 },
        { Base_Drink: null, Size: "Grande", Category: null, Base_Price: 3.75 },
    ];

    const result = parseMenu(mockInput);
    console.log(JSON.stringify(result, null, 2));
}

main();
