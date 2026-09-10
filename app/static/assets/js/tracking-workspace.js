
(function () {
  const DEFAULT_MESSAGES = {
    trackingEyebrow: "Estado do pedido",
    trackingTitle: "Acompanhe o seu pedido",
    trackingText: "Quando houver propostas, poderá escolher o transportador nesta página, sem login e sem instalar nada.",
    offersTitle: "Propostas",
    waitingTitle: "Ainda não recebemos propostas.",
    waitingText: "Estamos à procura de transportadores.",
    waitingNote: "Isto normalmente demora apenas alguns minutos.",
    closedRequestText: "Este pedido já não está ativo.",
    noOffersText: "Não recebemos propostas para este pedido.",
    viewStatus: "Ver estado",
    copyLink: "Copiar link",
    linkCopied: "Link copiado",
    shareWhatsApp: "Enviar por WhatsApp",
    newRequest: "← Novo pedido",
    viewOffers: "Ver ofertas",
    selectOffer: "Escolher esta oferta",
    confirmDeal: "Negócio confirmado",
    failDeal: "Não chegámos a acordo com o transportador",
    confirmationRecorded: "A sua confirmação foi registada. Aguardamos a confirmação do transportador.",
    confirmationCompleted: "A confirmação de ambas as partes foi registada. O transporte está confirmado.",
    completionPrompt: "O transporte foi concluído?",
    completionConfirm: "Transporte concluído",
    completionProblem: "Existe um problema",
    completionRecorded: "A sua resposta foi guardada. Aguardamos a confirmação do transportador.",
    completionProblemRecorded: "O problema foi registado. A CargoPT irá verificar a situação.",
    offersAvailable: "{count} oferta(s) disponível(eis)",
    defaultRoute: "Pedido CargoPT",
    waitingOffers: "A aguardar ofertas",
    statusCancelled: "Pedido cancelado",
    statusNoOffers: "Sem ofertas disponíveis",
    detailsTitle: "Detalhes do pedido",
    requestedDateLabel: "Data e hora",
    pickupLabel: "Origem",
    dropoffLabel: "Destino",
    floorLabel: "Piso",
    elevatorLabel: "Elevador",
    yesLabel: "Sim",
    noLabel: "Não",
    notProvidedLabel: "Não indicado",
    itemsLabel: "Itens",
    commentLabel: "Comentário",
    requirementsLabel: "Serviços e requisitos",
    assemblyLabel: "Montagem",
    packingLabel: "Embalamento",
    requestContactLabel: "Contacto do pedido",
    requestActionsTitle: "Gerir pedido",
    changeDateHelp: "Pode alterar a data antes de escolher um transportador.",
    repricingWarning: "Se já existirem propostas, serão fechadas e a CargoPT pedirá novos preços.",
    saveRequestedDate: "Alterar data",
    savingRequestedDate: "A alterar...",
    cancelRequest: "Cancelar pedido",
    cancellingRequest: "A cancelar...",
    confirmCancelRequest: "Tem a certeza de que pretende cancelar este pedido?",
    requestActionFailed: "Não foi possível guardar a alteração. Tente novamente.",
    coordinatedChange: "Depois de escolher um transportador, alterações e cancelamentos têm de ser coordenados com a CargoPT.",
    contactCargoPT: "Contactar a CargoPT",
    defaultCarrier: "Transportador",
    contactLabel: "Contacto",
    phoneLabel: "Telefone",
    telegramLabel: "Telegram",
    loadersLabel: "Ajudantes",
    tailLiftLabel: "Plataforma elevatória",
    craneLabel: "Grua",
    mobileLiftLabel: "Elevador exterior",
    failDealShort: "Não chegámos a acordo",
    selectedOfferLabel: "Oferta selecionada",
    priceLabel: "Preço",
    vehicleDetailsLabel: "Veículo e capacidade",
    vehicleLabel: "Veículo",
    payloadLabel: "Carga",
    volumeLabel: "Volume",
    equipmentLabel: "Equipamento",
    offerTermsLabel: "Condições da proposta",
    includedServicesLabel: "Serviços incluídos",
    possibleSurchargesLabel: "Possíveis extras",
    serviceWindowLabel: "Data / janela horária",
    estimateStatusLabel: "Tipo de preço",
    estimateFinalLabel: "Definitivo",
    estimateEstimateLabel: "Estimativa",
    carrierContactLabel: "Contacto do transportador",
    carrierNoteLabel: "Nota do transportador",
    shortLeadTimeWarning: "Faltam menos de três dias para o transporte. Por isso, o pedido não foi enviado automaticamente aos transportadores e ficou guardado para análise manual pela CargoPT. Para iniciar a procura automática, altere a data para pelo menos três dias a partir de agora.",
    shortLeadWaitingTitle: "Pedido em análise manual.",
    shortLeadWaitingText: "A equipa da CargoPT irá verificar o pedido.",
    shortLeadWaitingNote: "Não foram enviadas propostas automáticas aos transportadores."
  };

  function absoluteUrl(path) {
    return new URL(path, window.location.origin).toString();
  }

  function formatPrice(priceCents, locale) {
    if (priceCents == null) return "—";
    return new Intl.NumberFormat(locale || "pt-PT").format(priceCents / 100) + " €";
  }

  function getVisualState(entry) {
    const snapshot = entry.tracking_snapshot || {};
    const acceptedOffers = Array.isArray(snapshot.accepted_offers) ? snapshot.accepted_offers : [];
    if (snapshot.status === "cancelled") return "cancelled";
    if (["offers_exhausted", "expired_without_response"].includes(snapshot.status)) return "error";
    if (snapshot.status === "no_carriers_found") return "searching";
    if (snapshot.status === "completed") return "success";
    if (snapshot.client_confirmation_status === "confirmed" && snapshot.carrier_confirmation_status === "confirmed") return "success";
    if (snapshot.client_confirmation_status === "pending" || snapshot.carrier_confirmation_status === "pending") return "pending";
    if (["assigned_pending_confirmation", "assigned", "in_progress"].includes(snapshot.status)) return "pending";
    if (acceptedOffers.length > 0) return "success";
    if (["ready_for_matching", "matching", "offered", "manual_review_required"].includes(snapshot.status)) return "searching";
    return "searching";
  }

  function createOfferSection(className, title) {
    const section = document.createElement("section");
    section.className = `tracking-offer-section ${className}`;

    const heading = document.createElement("h4");
    heading.className = "tracking-offer-section-title";
    heading.textContent = title;

    section.appendChild(heading);
    return section;
  }

  function appendOfferDefinition(list, label, value) {
    if (
      value === null
      || value === undefined
      || value === ""
    ) return;

    const item = document.createElement("div");
    item.className = "tracking-offer-definition";

    const term = document.createElement("dt");
    term.textContent = label;

    const description = document.createElement("dd");
    description.textContent = String(value);

    item.append(term, description);
    list.appendChild(item);
  }

  function renderOffer(offer, entry, options, messages) {
    const card = document.createElement("article");
    card.className = "tracking-offer-card";

    const top = document.createElement("div");
    top.className = "tracking-offer-top";

    const identity = document.createElement("div");
    identity.className = "tracking-offer-identity";

    const companyName = offer.company_name || messages.defaultCarrier;

    const avatar = document.createElement("div");
    avatar.className = "tracking-offer-avatar";

    if (offer.logo_url) {
      const image = document.createElement("img");
      image.className = "tracking-offer-logo";
      image.src = offer.logo_url;
      image.alt = "";
      image.loading = "lazy";
      avatar.appendChild(image);
    } else {
      const initials = companyName
        .split(/\s+/)
        .filter(Boolean)
        .slice(0, 2)
        .map((part) => part.charAt(0).toUpperCase())
        .join("") || "C";
      avatar.textContent = initials;
      avatar.setAttribute("aria-hidden", "true");
    }

    const identityText = document.createElement("div");
    identityText.className = "tracking-offer-identity-text";

    const company = document.createElement("strong");
    company.className = "tracking-offer-company";
    company.textContent = companyName;

    identityText.appendChild(company);

    const profileMeta = [];
    if (offer.operating_regions) {
      const regionText = offer.operating_regions === "all_portugal"
        ? messages.allPortugalLabel
        : offer.operating_regions.split(",").join(", ");
      profileMeta.push(regionText);
    }
    if (offer.experience_since_year) {
      profileMeta.push(
        messages.experienceSinceLabel.replace(
          "{year}",
          String(offer.experience_since_year)
        )
      );
    }

    if (profileMeta.length) {
      const meta = document.createElement("span");
      meta.className = "tracking-offer-profile-meta";
      meta.textContent = profileMeta.join(" · ");
      identityText.appendChild(meta);
    }

    identity.append(avatar, identityText);

    const priceBlock = document.createElement("div");
    priceBlock.className = "tracking-offer-price-block";

    const priceLabel = document.createElement("span");
    priceLabel.className = "tracking-offer-price-label";
    priceLabel.textContent = messages.priceLabel;

    const price = document.createElement("strong");
    price.className = "tracking-offer-price";
    price.textContent = formatPrice(
      offer.price_cents,
      options.locale
    );

    priceBlock.append(priceLabel, price);
    top.append(identity, priceBlock);
    card.appendChild(top);

    const vehicleSection = createOfferSection(
      "tracking-offer-vehicle-section",
      messages.vehicleDetailsLabel
    );

    if (offer.vehicle_type) {
      const vehicleType = document.createElement("strong");
      vehicleType.className = "tracking-offer-vehicle-type";
      vehicleType.textContent = offer.vehicle_type;
      vehicleSection.appendChild(vehicleType);
    }

    const specifications = document.createElement("dl");
    specifications.className = "tracking-offer-spec-list";

    appendOfferDefinition(
      specifications,
      messages.payloadLabel,
      offer.payload_kg ? `${offer.payload_kg} kg` : null
    );

    appendOfferDefinition(
      specifications,
      messages.volumeLabel,
      offer.volume_m3 ? `${offer.volume_m3} m³` : null
    );

    appendOfferDefinition(
      specifications,
      messages.loadersLabel,
      offer.max_loaders || null
    );

    if (specifications.children.length) {
      vehicleSection.appendChild(specifications);
    }

    const equipment = [
      offer.has_tail_lift ? messages.tailLiftLabel : null,
      offer.has_crane ? messages.craneLabel : null,
      offer.has_mobile_lift
        ? messages.mobileLiftLabel
        : null
    ].filter(Boolean);

    if (equipment.length) {
      const equipmentBlock = document.createElement("div");
      equipmentBlock.className =
        "tracking-offer-equipment";

      const equipmentLabel = document.createElement("span");
      equipmentLabel.className =
        "tracking-offer-equipment-label";
      equipmentLabel.textContent = messages.equipmentLabel;

      const equipmentList = document.createElement("div");
      equipmentList.className =
        "tracking-offer-equipment-list";

      equipment.forEach((label) => {
        const chip = document.createElement("span");
        chip.className = "tracking-offer-equipment-chip";
        chip.textContent = label;
        equipmentList.appendChild(chip);
      });

      equipmentBlock.append(
        equipmentLabel,
        equipmentList
      );
      vehicleSection.appendChild(equipmentBlock);
    }

    card.appendChild(vehicleSection);

    const termsSection = createOfferSection(
      "tracking-offer-terms-section",
      messages.offerTermsLabel
    );
    const termsList = document.createElement("dl");
    termsList.className = "tracking-offer-spec-list";

    appendOfferDefinition(
      termsList,
      messages.includedServicesLabel,
      offer.included_services || messages.notProvidedLabel
    );
    appendOfferDefinition(
      termsList,
      messages.possibleSurchargesLabel,
      offer.possible_surcharges || messages.notProvidedLabel
    );
    appendOfferDefinition(
      termsList,
      messages.serviceWindowLabel,
      offer.service_window || messages.notProvidedLabel
    );
    appendOfferDefinition(
      termsList,
      messages.estimateStatusLabel,
      offer.estimate_status === "final"
        ? messages.estimateFinalLabel
        : offer.estimate_status === "estimate"
          ? messages.estimateEstimateLabel
          : messages.notProvidedLabel
    );

    termsSection.appendChild(termsList);
    card.appendChild(termsSection);

    const shouldShowCarrierContacts =
      entry.tracking_snapshot?.status !== "offered";

    const hasCarrierContacts =
      shouldShowCarrierContacts
      && (
        offer.contact_name
        || offer.phone
        || offer.telegram_username
      );

    if (hasCarrierContacts) {
      const contactSection = createOfferSection(
        "tracking-offer-contact-section",
        messages.carrierContactLabel
      );

      const contactList = document.createElement("dl");
      contactList.className =
        "tracking-offer-contact-list";

      appendOfferDefinition(
        contactList,
        messages.contactLabel,
        offer.contact_name
      );

      appendOfferDefinition(
        contactList,
        messages.phoneLabel,
        offer.phone
      );

      appendOfferDefinition(
        contactList,
        messages.telegramLabel,
        offer.telegram_username
          ? `@${offer.telegram_username}`
          : null
      );

      contactSection.appendChild(contactList);
      card.appendChild(contactSection);
    }

    if (offer.carrier_note) {
      const noteSection = createOfferSection(
        "tracking-offer-note-section",
        messages.carrierNoteLabel
      );

      const note = document.createElement("p");
      note.className = "tracking-offer-note";
      note.textContent = offer.carrier_note;

      noteSection.appendChild(note);
      card.appendChild(noteSection);
    }

    if (
      entry.tracking_snapshot?.status === "offered"
      && options.onSelectOffer
    ) {
      const button = document.createElement("button");
      button.className =
        "button button-small tracking-select-button";
      button.type = "button";
      button.textContent = messages.selectOffer;
      button.addEventListener(
        "click",
        () => options.onSelectOffer(
          offer.offer_id,
          button
        )
      );
      card.appendChild(button);
    }

    if (
      ["assigned_pending_confirmation", "assigned"].includes(
        entry.tracking_snapshot?.status
      )
      && options.onAssignmentAction
    ) {
      const failButton = document.createElement("button");
      failButton.className =
        "button button-small button-secondary "
        + "tracking-select-button tracking-assignment-fail";
      failButton.type = "button";
      failButton.textContent = messages.failDealShort;
      failButton.addEventListener(
        "click",
        () => options.onAssignmentAction(
          "fail",
          failButton
        )
      );
      card.appendChild(failButton);
    }

    return card;
  }

  function renderAssignmentActions(entry, options, messages) {
    const snapshot = entry.tracking_snapshot || {};
    if (
      !["assigned_pending_confirmation", "assigned"].includes(snapshot.status)
    ) return null;
    if (snapshot.client_confirmation_status !== "confirmed") return null;

    const bothConfirmed =
      snapshot.client_confirmation_status === "confirmed"
      && snapshot.carrier_confirmation_status === "confirmed";

    const actions = document.createElement("div");
    actions.className = "tracking-assignment-actions";

    const note = document.createElement("p");
    note.className = "tracking-assignment-note";
    note.textContent = bothConfirmed
      ? messages.confirmationCompleted
      : messages.confirmationRecorded;
    actions.appendChild(note);
    return actions;
  }

  function renderCompletionActions(entry, options, messages) {
    const snapshot = entry.tracking_snapshot || {};
    if (
      !["assigned", "in_progress"].includes(snapshot.status)
      || !snapshot.completion_prompted_at
    ) return null;

    const actions = document.createElement("div");
    actions.className = "tracking-assignment-actions";

    const note = document.createElement("p");
    note.className = "tracking-assignment-note";

    if (snapshot.client_completion_status === "problem") {
      note.textContent = messages.completionProblemRecorded;
      actions.appendChild(note);
      return actions;
    }
    if (snapshot.client_completion_status === "confirmed") {
      note.textContent = messages.completionRecorded;
      actions.appendChild(note);
      return actions;
    }
    if (!options.onCompletionAction) return null;

    note.textContent = messages.completionPrompt;
    actions.appendChild(note);

    const completionConfirmButton = document.createElement("button");
    completionConfirmButton.type = "button";
    completionConfirmButton.className = "button button-small tracking-select-button";
    completionConfirmButton.textContent = messages.completionConfirm;
    completionConfirmButton.addEventListener(
      "click",
      () => options.onCompletionAction("confirm", completionConfirmButton)
    );

    const problemButton = document.createElement("button");
    problemButton.type = "button";
    problemButton.className = "button button-small button-secondary tracking-select-button";
    problemButton.textContent = messages.completionProblem;
    problemButton.addEventListener(
      "click",
      () => options.onCompletionAction("problem", problemButton)
    );

    actions.append(completionConfirmButton, problemButton);
    return actions;
  }

  function getEmptyStateCopy(entry, messages) {
    const status = String(
      entry.tracking_snapshot?.status || ""
    );

    if (status === "cancelled") {
      return {
        title: messages.statusCancelled,
        text: messages.closedRequestText,
        note: ""
      };
    }

    if (
      status === "no_carriers_found"
      || status === "offers_exhausted"
      || status === "expired_without_response"
    ) {
      return {
        title: messages.statusNoOffers,
        text: messages.noOffersText,
        note: ""
      };
    }

    return {
      title: messages.waitingTitle,
      text: messages.waitingText,
      note: messages.waitingNote
    };
  }

  function renderWaitingState(entry, messages) {
    const copy = getEmptyStateCopy(entry, messages);

    const waiting = document.createElement("section");
    waiting.className = "tracking-waiting-state";

    const title = document.createElement("strong");
    title.className = "tracking-waiting-title";
    title.textContent = copy.title;

    const text = document.createElement("span");
    text.className = "tracking-waiting-text";
    text.textContent = copy.text;

    waiting.append(title, text);

    if (copy.note) {
      const note = document.createElement("span");
      note.className = "tracking-waiting-note";
      note.textContent = copy.note;
      waiting.appendChild(note);
    }

    return waiting;
  }

  const MANAGEABLE_REQUEST_STATUSES = new Set([
    "ready_for_matching",
    "matching",
    "offered",
    "unmatched",
    "no_carriers_found",
    "offers_exhausted",
    "expired_without_response",
    "manual_review_required"
  ]);

  function parseStoredRequestedDate(value) {
    if (!value) return null;
    const hasTimezone = /(?:Z|[+-]\d{2}:\d{2})$/i.test(value);
    const parsed = new Date(hasTimezone ? value : `${value}Z`);
    return Number.isNaN(parsed.getTime()) ? null : parsed;
  }

  function portugalDateParts(value) {
    const parsed = parseStoredRequestedDate(value);
    if (!parsed) return {date: "", time: ""};

    const parts = Object.fromEntries(
      new Intl.DateTimeFormat("en-CA", {
        timeZone: "Europe/Lisbon",
        year: "numeric",
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
        hourCycle: "h23"
      }).formatToParts(parsed).map((part) => [part.type, part.value])
    );

    return {
      date: `${parts.year}-${parts.month}-${parts.day}`,
      time: `${parts.hour}:${parts.minute}`
    };
  }

  function formatRequestedDate(value, locale, messages) {
    const parsed = parseStoredRequestedDate(value);
    if (!parsed) return messages.notProvidedLabel;
    return new Intl.DateTimeFormat(locale || "pt-PT", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone: "Europe/Lisbon"
    }).format(parsed);
  }

  function appendSummaryDefinition(list, label, value) {
    if (value === null || value === undefined || value === "") return;
    const item = document.createElement("div");
    item.className = "tracking-request-definition";
    const term = document.createElement("dt");
    term.textContent = label;
    const description = document.createElement("dd");
    description.textContent = String(value);
    item.append(term, description);
    list.appendChild(item);
  }

  function formatAddress(address, messages) {
    if (!address) return messages.notProvidedLabel;
    const lines = [address.normalized_address || address.raw_text];
    if (address.address_details) lines.push(address.address_details);
    if (address.floor !== null && address.floor !== undefined) {
      lines.push(`${messages.floorLabel}: ${address.floor}`);
    }
    if (address.has_elevator !== null && address.has_elevator !== undefined) {
      lines.push(
        `${messages.elevatorLabel}: ${address.has_elevator ? messages.yesLabel : messages.noLabel}`
      );
    }
    return lines.filter(Boolean).join(" · ");
  }

  function renderRequestSummary(entry, options, messages) {
    const details = entry.tracking_snapshot?.request_details;
    if (!details) return null;

    const section = document.createElement("section");
    section.id = "requestSummary";
    section.className = "tracking-request-summary";

    const title = document.createElement("h2");
    title.className = "tracking-request-summary-title";
    title.textContent = messages.detailsTitle;

    const list = document.createElement("dl");
    list.className = "tracking-request-summary-list";
    appendSummaryDefinition(
      list,
      messages.requestedDateLabel,
      formatRequestedDate(details.requested_date, options.locale, messages)
    );

    const pickup = details.addresses?.find((item) => item.kind === "pickup");
    const dropoff = details.addresses?.find((item) => item.kind === "dropoff");
    appendSummaryDefinition(list, messages.pickupLabel, formatAddress(pickup, messages));
    appendSummaryDefinition(list, messages.dropoffLabel, formatAddress(dropoff, messages));

    const itemSummary = (details.items || []).map((item) => {
      const quantity = item.quantity ? `${item.quantity} × ` : "";
      return `${quantity}${item.description}`;
    }).join("; ");
    appendSummaryDefinition(list, messages.itemsLabel, itemSummary);

    const requirements = [
      details.needs_assembly ? messages.assemblyLabel : null,
      details.needs_packing ? messages.packingLabel : null,
      details.needs_tail_lift ? messages.tailLiftLabel : null,
      details.needs_crane ? messages.craneLabel : null,
      details.needs_mobile_lift ? messages.mobileLiftLabel : null
    ].filter(Boolean);
    appendSummaryDefinition(
      list,
      messages.requirementsLabel,
      requirements.join(", ") || messages.notProvidedLabel
    );
    appendSummaryDefinition(list, messages.loadersLabel, details.required_loaders);
    appendSummaryDefinition(
      list,
      messages.payloadLabel,
      details.estimated_payload_kg == null ? null : `${details.estimated_payload_kg} kg`
    );
    appendSummaryDefinition(
      list,
      messages.volumeLabel,
      details.estimated_volume_m3 == null ? null : `${details.estimated_volume_m3} m³`
    );
    appendSummaryDefinition(list, messages.commentLabel, details.comment);

    const contact = [
      details.customer_name,
      details.customer_email,
      details.client_phone,
      details.client_whatsapp
    ].filter(Boolean).join(" · ");
    appendSummaryDefinition(list, messages.requestContactLabel, contact);
    section.append(title, list);
    return section;
  }

  function renderRequestActions(entry, options, messages) {
    const snapshot = entry.tracking_snapshot || {};
    const status = String(snapshot.status || "");
    const assigned = [
      "assigned_pending_confirmation",
      "assigned",
      "in_progress"
    ].includes(status);

    if (!assigned && !MANAGEABLE_REQUEST_STATUSES.has(status)) return null;

    const section = document.createElement("section");
    section.className = "tracking-request-actions";
    const title = document.createElement("h2");
    title.className = "tracking-request-summary-title";
    title.textContent = messages.requestActionsTitle;
    section.appendChild(title);

    if (assigned) {
      const note = document.createElement("p");
      note.className = "tracking-request-action-note";
      note.textContent = messages.coordinatedChange;
      const contact = document.createElement("a");
      contact.className = "button button-small button-secondary";
      contact.href = "mailto:hello@cargopt.pt";
      contact.textContent = messages.contactCargoPT;
      section.append(note, contact);
      return section;
    }

    const help = document.createElement("p");
    help.className = "tracking-request-action-note";
    help.textContent = status === "offered"
      ? messages.repricingWarning
      : messages.changeDateHelp;

    const form = document.createElement("form");
    form.id = "requestDateChange";
    form.className = "tracking-request-date-form";
    const storedDate = portugalDateParts(
      snapshot.request_details?.requested_date
    );
    const dateInput = document.createElement("input");
    dateInput.type = "date";
    dateInput.required = true;
    dateInput.value = storedDate.date;
    dateInput.setAttribute("aria-label", messages.requestedDateLabel);
    const timeInput = document.createElement("input");
    timeInput.type = "time";
    timeInput.required = true;
    timeInput.value = storedDate.time;
    timeInput.setAttribute("aria-label", messages.requestedDateLabel);
    const saveButton = document.createElement("button");
    saveButton.type = "submit";
    saveButton.className = "button button-small";
    saveButton.textContent = messages.saveRequestedDate;
    const feedback = document.createElement("p");
    feedback.className = "tracking-request-action-feedback";
    feedback.setAttribute("role", "status");

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      if (!form.reportValidity() || !options.onRequestedDateChange) return;
      feedback.textContent = "";
      saveButton.disabled = true;
      saveButton.textContent = messages.savingRequestedDate;
      try {
        await options.onRequestedDateChange(
          dateInput.value,
          timeInput.value,
          saveButton
        );
      } catch (error) {
        console.error(error);
        saveButton.disabled = false;
        saveButton.textContent = messages.saveRequestedDate;
        feedback.textContent = messages.requestActionFailed;
      }
    });

    const cancelButton = document.createElement("button");
    cancelButton.id = "requestCancel";
    cancelButton.type = "button";
    cancelButton.className = "button button-small button-secondary tracking-cancel-request";
    cancelButton.textContent = messages.cancelRequest;
    cancelButton.addEventListener("click", async () => {
      if (!options.onRequestCancel) return;
      if (!window.confirm(messages.confirmCancelRequest)) return;
      feedback.textContent = "";
      cancelButton.disabled = true;
      cancelButton.textContent = messages.cancellingRequest;
      try {
        await options.onRequestCancel(cancelButton);
      } catch (error) {
        console.error(error);
        cancelButton.disabled = false;
        cancelButton.textContent = messages.cancelRequest;
        feedback.textContent = messages.requestActionFailed;
      }
    });

    form.append(dateInput, timeInput, saveButton);
    section.append(help, form, cancelButton, feedback);
    return section;
  }

  function renderOffers(entry, options, messages) {
    const offers = entry.tracking_snapshot?.accepted_offers || [];

    const wrap = document.createElement("section");
    wrap.className = "tracking-offers";

    const offersTitle = document.createElement("strong");
    offersTitle.className = "tracking-offers-title";
    offersTitle.textContent =
      messages.offersTitle || messages.viewOffers;

    const offersList = document.createElement("div");
    offersList.className = "tracking-offers-list";

    offers.forEach((offer) => {
      offersList.appendChild(
        renderOffer(offer, entry, options, messages)
      );
    });

    wrap.append(offersTitle, offersList);
    return wrap;
  }

  function render(entry, options = {}) {
    const container = options.container;

    if (!container) {
      throw new Error("tracking workspace container is required");
    }

    const messages = {
      ...DEFAULT_MESSAGES,
      ...(options.messages || {})
    };

    const offers =
      entry.tracking_snapshot?.accepted_offers || [];

    container.textContent = "";

    const workspace = document.createElement("div");
    workspace.className = "tracking-workspace-content";

    const requestSummary = renderRequestSummary(
      entry,
      options,
      messages
    );
    if (requestSummary) workspace.appendChild(requestSummary);

    if (entry.tracking_snapshot?.short_lead_time_warning) {
      const warning = document.createElement("aside");
      warning.className = "tracking-short-lead-warning";
      warning.setAttribute("role", "status");
      warning.textContent = messages.shortLeadTimeWarning;
      workspace.appendChild(warning);
    }

    if (offers.length > 0 && !options.hideOffers) {
      workspace.appendChild(
        renderOffers(entry, options, messages)
      );
    } else {
      const waitingMessages = entry.tracking_snapshot?.short_lead_time_warning
        ? {
            ...messages,
            waitingTitle: messages.shortLeadWaitingTitle,
            waitingText: messages.shortLeadWaitingText,
            waitingNote: messages.shortLeadWaitingNote
          }
        : messages;
      workspace.appendChild(
        renderWaitingState(entry, waitingMessages)
      );
    }

    const assignmentActions = renderAssignmentActions(
      entry,
      options,
      messages
    );

    if (assignmentActions) {
      workspace.appendChild(assignmentActions);
    }

    const completionActions = renderCompletionActions(
      entry,
      options,
      messages
    );

    if (completionActions) {
      workspace.appendChild(completionActions);
    }

    const requestActions = renderRequestActions(
      entry,
      options,
      messages
    );
    if (requestActions) workspace.appendChild(requestActions);

    container.appendChild(workspace);
  }

  window.CargoPTTrackingWorkspace = {render, getVisualState};
})();
