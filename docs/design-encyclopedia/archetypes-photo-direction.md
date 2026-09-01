# Archetypes and Photo Director

## Site archetypes

| ID | Intents | Traits | Preferred silhouettes | Directions |
|---|---|---|---|---|
| `local_emergency_service` | emergency, phone | conversion_led, local, phone_first | urgent_local, phone_first_service | conversion_premium |
| `premium_residential` | renovation, residential | luxurious, trust_led, visual_led | premium_residential, editorial_residential | editorial_luxury, cinematic_luxury |
| `high_end_craft` | bespoke, craft | material_led, tactile, warm | craft_material_story, workshop_journey | warm_craft, material_editorial |
| `architectural_contracting` | architecture, contracting | architectural, project_led, technical | architectural_contracting, project_ledger | minimal_architecture, architectural_brutalist |
| `technical_expert` | expertise, technical | information_dense, technical, trust_led | technical_capabilities, specification_first | technical_spatial, minimal_architecture |
| `family_business` | local, relationship | local, trust_led, warm | family_trust, local_service_story | warm_craft, conversion_premium |
| `project_portfolio` | portfolio, projects | portfolio, project_led, visual_led | project_ledger, gallery_sequence | minimal_architecture, editorial_luxury |
| `luxury_renovation` | luxury, renovation | cinematic, luxurious, story_led | transformation_story, cinematic_residential | cinematic_luxury, editorial_luxury |
| `industrial_specialist` | b2b, industrial | industrial, information_dense, technical | industrial_capabilities, technical_capabilities | technical_spatial, architectural_brutalist |
| `conversion_first_local` | local, quote | conversion_led, local, service_led | local_conversion, quote_first_service | conversion_premium, minimal_architecture |
| `editorial_studio` | brand, editorial | asymmetric, editorial, story_led | editorial_manifesto, magazine_service | editorial_luxury, material_editorial |
| `warm_artisan` | craft, local | documentary, local, warm | warm_artisan, workshop_journey | warm_craft |
| `minimal_architecture` | minimal, projects | architectural, minimal, quiet | minimal_statement, project_ledger | minimal_architecture |
| `bold_local` | local, visibility | bold, conversion_led, service_led | bold_local, local_conversion | conversion_premium, architectural_brutalist |
| `documentary_craft` | craft, process | documentary, story_led, tactile | documentary_process, craft_material_story | warm_craft, material_editorial |
| `design_build` | build, design | architectural, project_led, story_led | design_build_journey, transformation_story | minimal_architecture, editorial_luxury |
| `heritage_craft` | heritage, restoration | editorial, material_led, warm | heritage_story, craft_material_story | material_editorial, warm_craft |
| `spatial_technical` | innovation, technical | futuristic, layered, technical | spatial_explainer, technical_capabilities | technical_spatial |
| `material_led` | finish, materials | material, tactile, visual_led | material_library, editorial_manifesto | material_editorial, warm_craft |
| `quiet_luxury` | calm, luxury | luxurious, minimal, quiet | quiet_luxury, premium_residential | editorial_luxury, minimal_architecture |

## Photo Director matrix

Profiles: 192 = 6 trades x 8 directions x 4 sections.

| Trade | Direction | Section | Orientation | Allowed roles | First query |
|---|---|---|---|---|---|
| plombier | `editorial_luxury` | hero | landscape | ambient, illustration | contemporary bathroom editorial natural light wide establishing image |
| plombier | `editorial_luxury` | gallery | mixed | ambient, illustration | contemporary bathroom editorial natural light visual sequence |
| plombier | `editorial_luxury` | about | portrait | ambient, illustration | contemporary bathroom editorial natural light workshop or process context |
| plombier | `editorial_luxury` | ambient | mixed | ambient, illustration | contemporary bathroom editorial natural light material atmosphere |
| plombier | `conversion_premium` | hero | landscape | ambient, illustration | contemporary bathroom professional residential wide establishing image |
| plombier | `conversion_premium` | gallery | mixed | ambient, illustration | contemporary bathroom professional residential visual sequence |
| plombier | `conversion_premium` | about | portrait | ambient, illustration | contemporary bathroom professional residential workshop or process context |
| plombier | `conversion_premium` | ambient | mixed | ambient, illustration | contemporary bathroom professional residential material atmosphere |
| plombier | `technical_spatial` | hero | landscape | ambient, illustration | contemporary bathroom technical architectural detail wide establishing image |
| plombier | `technical_spatial` | gallery | mixed | ambient, illustration | contemporary bathroom technical architectural detail visual sequence |
| plombier | `technical_spatial` | about | portrait | ambient, illustration | contemporary bathroom technical architectural detail workshop or process context |
| plombier | `technical_spatial` | ambient | mixed | ambient, illustration | contemporary bathroom technical architectural detail material atmosphere |
| plombier | `architectural_brutalist` | hero | landscape | ambient, illustration | contemporary bathroom raw monumental architecture wide establishing image |
| plombier | `architectural_brutalist` | gallery | mixed | ambient, illustration | contemporary bathroom raw monumental architecture visual sequence |
| plombier | `architectural_brutalist` | about | portrait | ambient, illustration | contemporary bathroom raw monumental architecture workshop or process context |
| plombier | `architectural_brutalist` | ambient | mixed | ambient, illustration | contemporary bathroom raw monumental architecture material atmosphere |
| plombier | `warm_craft` | hero | landscape | ambient, illustration | contemporary bathroom warm workshop craft wide establishing image |
| plombier | `warm_craft` | gallery | mixed | ambient, illustration | contemporary bathroom warm workshop craft visual sequence |
| plombier | `warm_craft` | about | portrait | ambient, illustration | contemporary bathroom warm workshop craft workshop or process context |
| plombier | `warm_craft` | ambient | mixed | ambient, illustration | contemporary bathroom warm workshop craft material atmosphere |
| plombier | `cinematic_luxury` | hero | landscape | ambient, illustration | contemporary bathroom cinematic luxury interior wide establishing image |
| plombier | `cinematic_luxury` | gallery | mixed | ambient, illustration | contemporary bathroom cinematic luxury interior visual sequence |
| plombier | `cinematic_luxury` | about | portrait | ambient, illustration | contemporary bathroom cinematic luxury interior workshop or process context |
| plombier | `cinematic_luxury` | ambient | mixed | ambient, illustration | contemporary bathroom cinematic luxury interior material atmosphere |
| plombier | `minimal_architecture` | hero | landscape | ambient, illustration | contemporary bathroom minimal contemporary architecture wide establishing image |
| plombier | `minimal_architecture` | gallery | mixed | ambient, illustration | contemporary bathroom minimal contemporary architecture visual sequence |
| plombier | `minimal_architecture` | about | portrait | ambient, illustration | contemporary bathroom minimal contemporary architecture workshop or process context |
| plombier | `minimal_architecture` | ambient | mixed | ambient, illustration | contemporary bathroom minimal contemporary architecture material atmosphere |
| plombier | `material_editorial` | hero | landscape | ambient, illustration | contemporary bathroom material texture editorial wide establishing image |
| plombier | `material_editorial` | gallery | mixed | ambient, illustration | contemporary bathroom material texture editorial visual sequence |
| plombier | `material_editorial` | about | portrait | ambient, illustration | contemporary bathroom material texture editorial workshop or process context |
| plombier | `material_editorial` | ambient | mixed | ambient, illustration | contemporary bathroom material texture editorial material atmosphere |
| peintre | `editorial_luxury` | hero | landscape | ambient, illustration | painted interior architecture editorial natural light wide establishing image |
| peintre | `editorial_luxury` | gallery | mixed | ambient, illustration | painted interior architecture editorial natural light visual sequence |
| peintre | `editorial_luxury` | about | portrait | ambient, illustration | painted interior architecture editorial natural light workshop or process context |
| peintre | `editorial_luxury` | ambient | mixed | ambient, illustration | painted interior architecture editorial natural light material atmosphere |
| peintre | `conversion_premium` | hero | landscape | ambient, illustration | painted interior architecture professional residential wide establishing image |
| peintre | `conversion_premium` | gallery | mixed | ambient, illustration | painted interior architecture professional residential visual sequence |
| peintre | `conversion_premium` | about | portrait | ambient, illustration | painted interior architecture professional residential workshop or process context |
| peintre | `conversion_premium` | ambient | mixed | ambient, illustration | painted interior architecture professional residential material atmosphere |
| peintre | `technical_spatial` | hero | landscape | ambient, illustration | painted interior architecture technical architectural detail wide establishing image |
| peintre | `technical_spatial` | gallery | mixed | ambient, illustration | painted interior architecture technical architectural detail visual sequence |
| peintre | `technical_spatial` | about | portrait | ambient, illustration | painted interior architecture technical architectural detail workshop or process context |
| peintre | `technical_spatial` | ambient | mixed | ambient, illustration | painted interior architecture technical architectural detail material atmosphere |
| peintre | `architectural_brutalist` | hero | landscape | ambient, illustration | painted interior architecture raw monumental architecture wide establishing image |
| peintre | `architectural_brutalist` | gallery | mixed | ambient, illustration | painted interior architecture raw monumental architecture visual sequence |
| peintre | `architectural_brutalist` | about | portrait | ambient, illustration | painted interior architecture raw monumental architecture workshop or process context |
| peintre | `architectural_brutalist` | ambient | mixed | ambient, illustration | painted interior architecture raw monumental architecture material atmosphere |
| peintre | `warm_craft` | hero | landscape | ambient, illustration | painted interior architecture warm workshop craft wide establishing image |
| peintre | `warm_craft` | gallery | mixed | ambient, illustration | painted interior architecture warm workshop craft visual sequence |
| peintre | `warm_craft` | about | portrait | ambient, illustration | painted interior architecture warm workshop craft workshop or process context |
| peintre | `warm_craft` | ambient | mixed | ambient, illustration | painted interior architecture warm workshop craft material atmosphere |
| peintre | `cinematic_luxury` | hero | landscape | ambient, illustration | painted interior architecture cinematic luxury interior wide establishing image |
| peintre | `cinematic_luxury` | gallery | mixed | ambient, illustration | painted interior architecture cinematic luxury interior visual sequence |
| peintre | `cinematic_luxury` | about | portrait | ambient, illustration | painted interior architecture cinematic luxury interior workshop or process context |
| peintre | `cinematic_luxury` | ambient | mixed | ambient, illustration | painted interior architecture cinematic luxury interior material atmosphere |
| peintre | `minimal_architecture` | hero | landscape | ambient, illustration | painted interior architecture minimal contemporary architecture wide establishing image |
| peintre | `minimal_architecture` | gallery | mixed | ambient, illustration | painted interior architecture minimal contemporary architecture visual sequence |
| peintre | `minimal_architecture` | about | portrait | ambient, illustration | painted interior architecture minimal contemporary architecture workshop or process context |
| peintre | `minimal_architecture` | ambient | mixed | ambient, illustration | painted interior architecture minimal contemporary architecture material atmosphere |
| peintre | `material_editorial` | hero | landscape | ambient, illustration | painted interior architecture material texture editorial wide establishing image |
| peintre | `material_editorial` | gallery | mixed | ambient, illustration | painted interior architecture material texture editorial visual sequence |
| peintre | `material_editorial` | about | portrait | ambient, illustration | painted interior architecture material texture editorial workshop or process context |
| peintre | `material_editorial` | ambient | mixed | ambient, illustration | painted interior architecture material texture editorial material atmosphere |
| macon | `editorial_luxury` | hero | landscape | ambient, illustration | masonry construction detail editorial natural light wide establishing image |
| macon | `editorial_luxury` | gallery | mixed | ambient, illustration | masonry construction detail editorial natural light visual sequence |
| macon | `editorial_luxury` | about | portrait | ambient, illustration | masonry construction detail editorial natural light workshop or process context |
| macon | `editorial_luxury` | ambient | mixed | ambient, illustration | masonry construction detail editorial natural light material atmosphere |
| macon | `conversion_premium` | hero | landscape | ambient, illustration | masonry construction detail professional residential wide establishing image |
| macon | `conversion_premium` | gallery | mixed | ambient, illustration | masonry construction detail professional residential visual sequence |
| macon | `conversion_premium` | about | portrait | ambient, illustration | masonry construction detail professional residential workshop or process context |
| macon | `conversion_premium` | ambient | mixed | ambient, illustration | masonry construction detail professional residential material atmosphere |
| macon | `technical_spatial` | hero | landscape | ambient, illustration | masonry construction detail technical architectural detail wide establishing image |
| macon | `technical_spatial` | gallery | mixed | ambient, illustration | masonry construction detail technical architectural detail visual sequence |
| macon | `technical_spatial` | about | portrait | ambient, illustration | masonry construction detail technical architectural detail workshop or process context |
| macon | `technical_spatial` | ambient | mixed | ambient, illustration | masonry construction detail technical architectural detail material atmosphere |
| macon | `architectural_brutalist` | hero | landscape | ambient, illustration | masonry construction detail raw monumental architecture wide establishing image |
| macon | `architectural_brutalist` | gallery | mixed | ambient, illustration | masonry construction detail raw monumental architecture visual sequence |
| macon | `architectural_brutalist` | about | portrait | ambient, illustration | masonry construction detail raw monumental architecture workshop or process context |
| macon | `architectural_brutalist` | ambient | mixed | ambient, illustration | masonry construction detail raw monumental architecture material atmosphere |
| macon | `warm_craft` | hero | landscape | ambient, illustration | masonry construction detail warm workshop craft wide establishing image |
| macon | `warm_craft` | gallery | mixed | ambient, illustration | masonry construction detail warm workshop craft visual sequence |
| macon | `warm_craft` | about | portrait | ambient, illustration | masonry construction detail warm workshop craft workshop or process context |
| macon | `warm_craft` | ambient | mixed | ambient, illustration | masonry construction detail warm workshop craft material atmosphere |
| macon | `cinematic_luxury` | hero | landscape | ambient, illustration | masonry construction detail cinematic luxury interior wide establishing image |
| macon | `cinematic_luxury` | gallery | mixed | ambient, illustration | masonry construction detail cinematic luxury interior visual sequence |
| macon | `cinematic_luxury` | about | portrait | ambient, illustration | masonry construction detail cinematic luxury interior workshop or process context |
| macon | `cinematic_luxury` | ambient | mixed | ambient, illustration | masonry construction detail cinematic luxury interior material atmosphere |
| macon | `minimal_architecture` | hero | landscape | ambient, illustration | masonry construction detail minimal contemporary architecture wide establishing image |
| macon | `minimal_architecture` | gallery | mixed | ambient, illustration | masonry construction detail minimal contemporary architecture visual sequence |
| macon | `minimal_architecture` | about | portrait | ambient, illustration | masonry construction detail minimal contemporary architecture workshop or process context |
| macon | `minimal_architecture` | ambient | mixed | ambient, illustration | masonry construction detail minimal contemporary architecture material atmosphere |
| macon | `material_editorial` | hero | landscape | ambient, illustration | masonry construction detail material texture editorial wide establishing image |
| macon | `material_editorial` | gallery | mixed | ambient, illustration | masonry construction detail material texture editorial visual sequence |
| macon | `material_editorial` | about | portrait | ambient, illustration | masonry construction detail material texture editorial workshop or process context |
| macon | `material_editorial` | ambient | mixed | ambient, illustration | masonry construction detail material texture editorial material atmosphere |
| electricien | `editorial_luxury` | hero | landscape | ambient, illustration | architectural lighting editorial natural light wide establishing image |
| electricien | `editorial_luxury` | gallery | mixed | ambient, illustration | architectural lighting editorial natural light visual sequence |
| electricien | `editorial_luxury` | about | portrait | ambient, illustration | architectural lighting editorial natural light workshop or process context |
| electricien | `editorial_luxury` | ambient | mixed | ambient, illustration | architectural lighting editorial natural light material atmosphere |
| electricien | `conversion_premium` | hero | landscape | ambient, illustration | architectural lighting professional residential wide establishing image |
| electricien | `conversion_premium` | gallery | mixed | ambient, illustration | architectural lighting professional residential visual sequence |
| electricien | `conversion_premium` | about | portrait | ambient, illustration | architectural lighting professional residential workshop or process context |
| electricien | `conversion_premium` | ambient | mixed | ambient, illustration | architectural lighting professional residential material atmosphere |
| electricien | `technical_spatial` | hero | landscape | ambient, illustration | architectural lighting technical architectural detail wide establishing image |
| electricien | `technical_spatial` | gallery | mixed | ambient, illustration | architectural lighting technical architectural detail visual sequence |
| electricien | `technical_spatial` | about | portrait | ambient, illustration | architectural lighting technical architectural detail workshop or process context |
| electricien | `technical_spatial` | ambient | mixed | ambient, illustration | architectural lighting technical architectural detail material atmosphere |
| electricien | `architectural_brutalist` | hero | landscape | ambient, illustration | architectural lighting raw monumental architecture wide establishing image |
| electricien | `architectural_brutalist` | gallery | mixed | ambient, illustration | architectural lighting raw monumental architecture visual sequence |
| electricien | `architectural_brutalist` | about | portrait | ambient, illustration | architectural lighting raw monumental architecture workshop or process context |
| electricien | `architectural_brutalist` | ambient | mixed | ambient, illustration | architectural lighting raw monumental architecture material atmosphere |
| electricien | `warm_craft` | hero | landscape | ambient, illustration | architectural lighting warm workshop craft wide establishing image |
| electricien | `warm_craft` | gallery | mixed | ambient, illustration | architectural lighting warm workshop craft visual sequence |
| electricien | `warm_craft` | about | portrait | ambient, illustration | architectural lighting warm workshop craft workshop or process context |
| electricien | `warm_craft` | ambient | mixed | ambient, illustration | architectural lighting warm workshop craft material atmosphere |
| electricien | `cinematic_luxury` | hero | landscape | ambient, illustration | architectural lighting cinematic luxury interior wide establishing image |
| electricien | `cinematic_luxury` | gallery | mixed | ambient, illustration | architectural lighting cinematic luxury interior visual sequence |
| electricien | `cinematic_luxury` | about | portrait | ambient, illustration | architectural lighting cinematic luxury interior workshop or process context |
| electricien | `cinematic_luxury` | ambient | mixed | ambient, illustration | architectural lighting cinematic luxury interior material atmosphere |
| electricien | `minimal_architecture` | hero | landscape | ambient, illustration | architectural lighting minimal contemporary architecture wide establishing image |
| electricien | `minimal_architecture` | gallery | mixed | ambient, illustration | architectural lighting minimal contemporary architecture visual sequence |
| electricien | `minimal_architecture` | about | portrait | ambient, illustration | architectural lighting minimal contemporary architecture workshop or process context |
| electricien | `minimal_architecture` | ambient | mixed | ambient, illustration | architectural lighting minimal contemporary architecture material atmosphere |
| electricien | `material_editorial` | hero | landscape | ambient, illustration | architectural lighting material texture editorial wide establishing image |
| electricien | `material_editorial` | gallery | mixed | ambient, illustration | architectural lighting material texture editorial visual sequence |
| electricien | `material_editorial` | about | portrait | ambient, illustration | architectural lighting material texture editorial workshop or process context |
| electricien | `material_editorial` | ambient | mixed | ambient, illustration | architectural lighting material texture editorial material atmosphere |
| menuisier | `editorial_luxury` | hero | landscape | ambient, illustration | custom joinery interior editorial natural light wide establishing image |
| menuisier | `editorial_luxury` | gallery | mixed | ambient, illustration | custom joinery interior editorial natural light visual sequence |
| menuisier | `editorial_luxury` | about | portrait | ambient, illustration | custom joinery interior editorial natural light workshop or process context |
| menuisier | `editorial_luxury` | ambient | mixed | ambient, illustration | custom joinery interior editorial natural light material atmosphere |
| menuisier | `conversion_premium` | hero | landscape | ambient, illustration | custom joinery interior professional residential wide establishing image |
| menuisier | `conversion_premium` | gallery | mixed | ambient, illustration | custom joinery interior professional residential visual sequence |
| menuisier | `conversion_premium` | about | portrait | ambient, illustration | custom joinery interior professional residential workshop or process context |
| menuisier | `conversion_premium` | ambient | mixed | ambient, illustration | custom joinery interior professional residential material atmosphere |
| menuisier | `technical_spatial` | hero | landscape | ambient, illustration | custom joinery interior technical architectural detail wide establishing image |
| menuisier | `technical_spatial` | gallery | mixed | ambient, illustration | custom joinery interior technical architectural detail visual sequence |
| menuisier | `technical_spatial` | about | portrait | ambient, illustration | custom joinery interior technical architectural detail workshop or process context |
| menuisier | `technical_spatial` | ambient | mixed | ambient, illustration | custom joinery interior technical architectural detail material atmosphere |
| menuisier | `architectural_brutalist` | hero | landscape | ambient, illustration | custom joinery interior raw monumental architecture wide establishing image |
| menuisier | `architectural_brutalist` | gallery | mixed | ambient, illustration | custom joinery interior raw monumental architecture visual sequence |
| menuisier | `architectural_brutalist` | about | portrait | ambient, illustration | custom joinery interior raw monumental architecture workshop or process context |
| menuisier | `architectural_brutalist` | ambient | mixed | ambient, illustration | custom joinery interior raw monumental architecture material atmosphere |
| menuisier | `warm_craft` | hero | landscape | ambient, illustration | custom joinery interior warm workshop craft wide establishing image |
| menuisier | `warm_craft` | gallery | mixed | ambient, illustration | custom joinery interior warm workshop craft visual sequence |
| menuisier | `warm_craft` | about | portrait | ambient, illustration | custom joinery interior warm workshop craft workshop or process context |
| menuisier | `warm_craft` | ambient | mixed | ambient, illustration | custom joinery interior warm workshop craft material atmosphere |
| menuisier | `cinematic_luxury` | hero | landscape | ambient, illustration | custom joinery interior cinematic luxury interior wide establishing image |
| menuisier | `cinematic_luxury` | gallery | mixed | ambient, illustration | custom joinery interior cinematic luxury interior visual sequence |
| menuisier | `cinematic_luxury` | about | portrait | ambient, illustration | custom joinery interior cinematic luxury interior workshop or process context |
| menuisier | `cinematic_luxury` | ambient | mixed | ambient, illustration | custom joinery interior cinematic luxury interior material atmosphere |
| menuisier | `minimal_architecture` | hero | landscape | ambient, illustration | custom joinery interior minimal contemporary architecture wide establishing image |
| menuisier | `minimal_architecture` | gallery | mixed | ambient, illustration | custom joinery interior minimal contemporary architecture visual sequence |
| menuisier | `minimal_architecture` | about | portrait | ambient, illustration | custom joinery interior minimal contemporary architecture workshop or process context |
| menuisier | `minimal_architecture` | ambient | mixed | ambient, illustration | custom joinery interior minimal contemporary architecture material atmosphere |
| menuisier | `material_editorial` | hero | landscape | ambient, illustration | custom joinery interior material texture editorial wide establishing image |
| menuisier | `material_editorial` | gallery | mixed | ambient, illustration | custom joinery interior material texture editorial visual sequence |
| menuisier | `material_editorial` | about | portrait | ambient, illustration | custom joinery interior material texture editorial workshop or process context |
| menuisier | `material_editorial` | ambient | mixed | ambient, illustration | custom joinery interior material texture editorial material atmosphere |
| renovateur | `editorial_luxury` | hero | landscape | ambient, illustration | residential renovation interior editorial natural light wide establishing image |
| renovateur | `editorial_luxury` | gallery | mixed | ambient, illustration | residential renovation interior editorial natural light visual sequence |
| renovateur | `editorial_luxury` | about | portrait | ambient, illustration | residential renovation interior editorial natural light workshop or process context |
| renovateur | `editorial_luxury` | ambient | mixed | ambient, illustration | residential renovation interior editorial natural light material atmosphere |
| renovateur | `conversion_premium` | hero | landscape | ambient, illustration | residential renovation interior professional residential wide establishing image |
| renovateur | `conversion_premium` | gallery | mixed | ambient, illustration | residential renovation interior professional residential visual sequence |
| renovateur | `conversion_premium` | about | portrait | ambient, illustration | residential renovation interior professional residential workshop or process context |
| renovateur | `conversion_premium` | ambient | mixed | ambient, illustration | residential renovation interior professional residential material atmosphere |
| renovateur | `technical_spatial` | hero | landscape | ambient, illustration | residential renovation interior technical architectural detail wide establishing image |
| renovateur | `technical_spatial` | gallery | mixed | ambient, illustration | residential renovation interior technical architectural detail visual sequence |
| renovateur | `technical_spatial` | about | portrait | ambient, illustration | residential renovation interior technical architectural detail workshop or process context |
| renovateur | `technical_spatial` | ambient | mixed | ambient, illustration | residential renovation interior technical architectural detail material atmosphere |
| renovateur | `architectural_brutalist` | hero | landscape | ambient, illustration | residential renovation interior raw monumental architecture wide establishing image |
| renovateur | `architectural_brutalist` | gallery | mixed | ambient, illustration | residential renovation interior raw monumental architecture visual sequence |
| renovateur | `architectural_brutalist` | about | portrait | ambient, illustration | residential renovation interior raw monumental architecture workshop or process context |
| renovateur | `architectural_brutalist` | ambient | mixed | ambient, illustration | residential renovation interior raw monumental architecture material atmosphere |
| renovateur | `warm_craft` | hero | landscape | ambient, illustration | residential renovation interior warm workshop craft wide establishing image |
| renovateur | `warm_craft` | gallery | mixed | ambient, illustration | residential renovation interior warm workshop craft visual sequence |
| renovateur | `warm_craft` | about | portrait | ambient, illustration | residential renovation interior warm workshop craft workshop or process context |
| renovateur | `warm_craft` | ambient | mixed | ambient, illustration | residential renovation interior warm workshop craft material atmosphere |
| renovateur | `cinematic_luxury` | hero | landscape | ambient, illustration | residential renovation interior cinematic luxury interior wide establishing image |
| renovateur | `cinematic_luxury` | gallery | mixed | ambient, illustration | residential renovation interior cinematic luxury interior visual sequence |
| renovateur | `cinematic_luxury` | about | portrait | ambient, illustration | residential renovation interior cinematic luxury interior workshop or process context |
| renovateur | `cinematic_luxury` | ambient | mixed | ambient, illustration | residential renovation interior cinematic luxury interior material atmosphere |
| renovateur | `minimal_architecture` | hero | landscape | ambient, illustration | residential renovation interior minimal contemporary architecture wide establishing image |
| renovateur | `minimal_architecture` | gallery | mixed | ambient, illustration | residential renovation interior minimal contemporary architecture visual sequence |
| renovateur | `minimal_architecture` | about | portrait | ambient, illustration | residential renovation interior minimal contemporary architecture workshop or process context |
| renovateur | `minimal_architecture` | ambient | mixed | ambient, illustration | residential renovation interior minimal contemporary architecture material atmosphere |
| renovateur | `material_editorial` | hero | landscape | ambient, illustration | residential renovation interior material texture editorial wide establishing image |
| renovateur | `material_editorial` | gallery | mixed | ambient, illustration | residential renovation interior material texture editorial visual sequence |
| renovateur | `material_editorial` | about | portrait | ambient, illustration | residential renovation interior material texture editorial workshop or process context |
| renovateur | `material_editorial` | ambient | mixed | ambient, illustration | residential renovation interior material texture editorial material atmosphere |
