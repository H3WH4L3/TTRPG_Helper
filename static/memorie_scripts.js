
document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("memories");
    const addBtn = document.getElementById("add-memorie");

    if (!container) {
        console.log("No #memories container found");
        return;
    }

    // Кнопка Add
    if (addBtn) {
        addBtn.addEventListener("click", () => {
            const firstBlock = container.querySelector(".memorie-block");
            if (!firstBlock) {
                console.log("No .memorie-block to clone");
                return;
            }

            const clone = firstBlock.cloneNode(true);

            // Очищаем все инпуты
            clone.querySelectorAll("input").forEach((input) => {
                input.value = "";
            });

            // Чистим ошибки в клоне
            clone.querySelectorAll(".error").forEach((err) => err.remove());

            container.appendChild(clone);
        });
    }

    //  Кнопка Remove
    container.addEventListener("click", (event) => {
        const removeBtn = event.target.closest(".remove");
        if (!removeBtn) return;

        const blocks = container.querySelectorAll(".memorie-block");
        const block = removeBtn.closest(".memorie-block");

        if (!block) return;

        if (blocks.length > 1) {
            block.remove();
        } else {
            // Последний блок — очищаем, но не удаляем
            block.querySelectorAll("input").forEach((input) => {
                input.value = "";
            });
            block.querySelectorAll(".error").forEach((err) => err.remove());
        }
    });
});
