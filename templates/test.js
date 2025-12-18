
const RENDER = {
    items(list) {
        return list.map(x => `
        <div class="card">
            <div class="title">${x.name_ru ?? "—"}</div>
            <div>Категория: ${x.category ?? ""}</div>
            <div>Эффект: ${x.effect ?? ""}</div>
            <div>Кол-во: ${x.counts ?? ""} | Цена: ${x.cost ?? ""}</div>
        </div>
        `).join("") || "<p>Пусто</p>";
    },

    skills(list) {
        return list.map(x => `
        <div class="card">
            <div class="title">${x.name_ru ?? "—"}</div>
            <div>${x.desc_ru ?? ""}</div>
        </div>
        `).join("") || "<p>Пусто</p>";
    },


    armors(list) {
        return list.map(x => `
        <div class="armor-block">
            <div class="name">${x.name_ru ?? "-"}</div >
            <div class="level">${x.armor_level ?? ""}</div>
            <div class="effect">${x.effect ?? ""}</div>
        </div >
    `).join("") || "<p>Пусто</p>";
    },
