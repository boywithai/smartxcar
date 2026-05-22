(function () {
  const socket = io();

  const carStatus = document.getElementById("car-status");
  const socketStatus = document.getElementById("socket-status");
  const distanceValue = document.getElementById("distance-value");
  const rainValue = document.getElementById("rain-value");
  const lastMessage = document.getElementById("last-message");
  const directionButtons = Array.from(document.querySelectorAll("[data-drive]"));
  const stopButton = document.querySelector("[data-stop]");
  const hornButton = document.querySelector("[data-horn]");
  const headlightsButton = document.querySelector("[data-headlights]");
  const flashButton = document.querySelector("[data-flash]");
  const wiperSelect = document.querySelector("[data-wiper]");
  const controls = [
    ...directionButtons,
    stopButton,
    hornButton,
    headlightsButton,
    flashButton,
    wiperSelect,
  ].filter(Boolean);

  let carOnline = false;
  let driveInterval = null;
  let activeDirection = null;
  let activeDirectionButton = null;
  let activeDirectionPointerId = null;
  let hornActive = false;
  let hornPointerId = null;
  let headlightsOn = false;

  function setLastMessage(message) {
    lastMessage.textContent = message;
  }

  function sendDrive(command) {
    socket.emit("drive_command", { command });
  }

  function sendAccessory(accessory, state) {
    socket.emit("accessory_command", { accessory, state });
  }

  function isPointerInsideElement(element, event) {
    if (!element) {
      return false;
    }

    const rect = element.getBoundingClientRect();
    return (
      event.clientX >= rect.left &&
      event.clientX <= rect.right &&
      event.clientY >= rect.top &&
      event.clientY <= rect.bottom
    );
  }

  function resetWiperUi() {
    if (wiperSelect) {
      wiperSelect.value = "0";
    }
  }

  function updateControls() {
    controls.forEach((control) => {
      control.disabled = !carOnline;
    });
  }

  function clearDriveInterval(sendStop) {
    const hadActiveDrive = Boolean(driveInterval || activeDirection);

    if (driveInterval) {
      clearInterval(driveInterval);
      driveInterval = null;
    }

    activeDirection = null;
    activeDirectionButton = null;
    activeDirectionPointerId = null;

    if (sendStop && hadActiveDrive && carOnline && socket.connected) {
      sendDrive("stop");
    }
  }

  function stopHorn(sendOff) {
    const hadActiveHorn = hornActive;

    hornActive = false;
    hornPointerId = null;

    if (sendOff && hadActiveHorn && carOnline && socket.connected) {
      sendAccessory("horn", "off");
    }
  }

  function setCarOnline(online) {
    carOnline = online;
    carStatus.textContent = online ? "Araç Bağlı" : "Araç Çevrimdışı";
    carStatus.classList.toggle("online", online);
    carStatus.classList.toggle("offline", !online);
    updateControls();

    if (!online) {
      clearDriveInterval(false);
      stopHorn(false);
      resetWiperUi();
      setLastMessage("Araç çevrimdışı.");
    }
  }

  function startDirection(command, button, pointerId) {
    if (!carOnline || !socket.connected) {
      return;
    }

    clearDriveInterval(Boolean(activeDirection));
    activeDirection = command;
    activeDirectionButton = button;
    activeDirectionPointerId = pointerId;
    sendDrive(command);
    driveInterval = window.setInterval(() => {
      if (activeDirection === command && carOnline && socket.connected) {
        sendDrive(command);
      }
    }, 250);
  }

  function handleDirectionPointerEnd(event) {
    if (activeDirectionPointerId === null || event.pointerId === activeDirectionPointerId) {
      clearDriveInterval(true);
    }
  }

  directionButtons.forEach((button) => {
    button.addEventListener("pointerdown", (event) => {
      if (event.pointerType === "mouse" && event.button !== 0) {
        return;
      }

      event.preventDefault();
      button.setPointerCapture?.(event.pointerId);
      startDirection(button.dataset.drive, button, event.pointerId);
    });

    button.addEventListener("pointerup", (event) => {
      event.preventDefault();
      handleDirectionPointerEnd(event);
    });

    button.addEventListener("pointercancel", (event) => {
      event.preventDefault();
      handleDirectionPointerEnd(event);
    });

    button.addEventListener("contextmenu", (event) => event.preventDefault());
  });

  window.addEventListener(
    "pointermove",
    (event) => {
      if (
        activeDirectionPointerId !== null &&
        event.pointerId === activeDirectionPointerId &&
        !isPointerInsideElement(activeDirectionButton, event)
      ) {
        clearDriveInterval(true);
      }

      if (
        hornPointerId !== null &&
        event.pointerId === hornPointerId &&
        !isPointerInsideElement(hornButton, event)
      ) {
        stopHorn(true);
      }
    },
    { passive: true }
  );

  window.addEventListener("pointerup", handleDirectionPointerEnd);
  window.addEventListener("pointercancel", handleDirectionPointerEnd);

  stopButton.addEventListener("click", () => {
    clearDriveInterval(false);
    if (carOnline && socket.connected) {
      sendDrive("stop");
      setLastMessage("Acil dur komutu gönderildi.");
    }
  });

  hornButton.addEventListener("pointerdown", (event) => {
    if (event.pointerType === "mouse" && event.button !== 0) {
      return;
    }

    event.preventDefault();
    hornButton.setPointerCapture?.(event.pointerId);

    if (carOnline && socket.connected) {
      stopHorn(true);
      hornActive = true;
      hornPointerId = event.pointerId;
      sendAccessory("horn", "on");
    }
  });

  hornButton.addEventListener("pointerup", (event) => {
    event.preventDefault();
    if (hornPointerId === null || event.pointerId === hornPointerId) {
      stopHorn(true);
    }
  });

  hornButton.addEventListener("pointercancel", (event) => {
    event.preventDefault();
    if (hornPointerId === null || event.pointerId === hornPointerId) {
      stopHorn(true);
    }
  });

  window.addEventListener("pointerup", (event) => {
    if (hornPointerId === null || event.pointerId === hornPointerId) {
      stopHorn(true);
    }
  });

  window.addEventListener("pointercancel", (event) => {
    if (hornPointerId === null || event.pointerId === hornPointerId) {
      stopHorn(true);
    }
  });

  hornButton.addEventListener("contextmenu", (event) => event.preventDefault());

  headlightsButton.addEventListener("click", () => {
    if (!carOnline || !socket.connected) {
      return;
    }

    headlightsOn = !headlightsOn;
    headlightsButton.setAttribute("aria-pressed", String(headlightsOn));
    headlightsButton.textContent = headlightsOn ? "Far Açık" : "Far Kapalı";
    sendAccessory("headlights", headlightsOn ? "on" : "off");
  });

  flashButton.addEventListener("click", () => {
    if (carOnline && socket.connected) {
      sendAccessory("flash", "trigger");
    }
  });

  wiperSelect.addEventListener("change", () => {
    if (carOnline && socket.connected) {
      sendAccessory("wiper", Number(wiperSelect.value));
    }
  });

  window.addEventListener("blur", () => {
    clearDriveInterval(true);
    stopHorn(true);
  });

  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      clearDriveInterval(true);
      stopHorn(true);
    }
  });

  socket.on("connect", () => {
    socketStatus.textContent = "Panel bağlı";
  });

  socket.on("disconnect", () => {
    socketStatus.textContent = "Panel bağlantısı koptu";
    clearDriveInterval(false);
    stopHorn(false);
    resetWiperUi();
    setCarOnline(false);
  });

  socket.on("car_status", (data) => {
    setCarOnline(Boolean(data.online));
  });

  socket.on("telemetry_update", (data) => {
    distanceValue.textContent =
      typeof data.distance_cm === "number" ? `${data.distance_cm.toFixed(1)} cm` : "Veri bekleniyor";
    rainValue.textContent = data.raining ? "Yağış var" : "Yağış yok";
  });

  socket.on("command_result", (data) => {
    setLastMessage(`${data.command_type}: ${data.command} - ${data.status} - ${data.message}`);
  });

  socket.on("status_message", (data) => {
    setLastMessage(data.message || "İşlem tamamlanamadı.");
  });

  updateControls();
})();
