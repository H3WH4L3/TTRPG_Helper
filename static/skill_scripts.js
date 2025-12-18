document.addEventListener("DOMContentLoaded", () => {
    const container = document.getElementById("skills");
    const addBtn = document.getElementById("add-skill");

    if (!container || !addBtn) return;

    // Кнопка "+"
    addBtn.addEventListener("click", () => {
        const firstBlock = container.querySelector(".main-block");
        if (!firstBlock) return;

        const clone = firstBlock.cloneNode(true);

        clone.querySelectorAll("input").forEach((input) => {
            input.value = "";
        });

        clone.querySelectorAll(".error").forEach((err) => err.remove());

        container.appendChild(clone);
    });

    // Кнопка "-"
    container.addEventListener("click", (event) => {
        const removeBtn = event.target.closest(".remove");
        if (!removeBtn) return;

        const blocks = container.querySelectorAll(".main-block");
        const block = removeBtn.closest(".main-block");
        if (!block) return;

        if (blocks.length > 1) {
            block.remove();
        } else {
            block.querySelectorAll("input").forEach((input) => {
                input.value = "";
            });
            block.querySelectorAll(".error").forEach((err) => err.remove());
        }
    });
});
