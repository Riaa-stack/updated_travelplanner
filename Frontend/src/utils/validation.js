// Shared client-side validation helpers. Date-only values stay as YYYY-MM-DD strings
// to avoid UTC conversions shifting the user's selected calendar day.
export function getLocalDateString(date = new Date()) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function validateTripDates(startDate, endDate, today = getLocalDateString()) {
  const errors = {};
  const validDate = (value) => {
    if (!/^\d{4}-\d{2}-\d{2}$/.test(value || '')) return false;
    const [year, month, day] = value.split('-').map(Number);
    const date = new Date(year, month - 1, day);
    return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
  };

  if (!startDate) errors.startDate = 'Start date is required.';
  else if (!validDate(startDate)) errors.startDate = 'Enter a valid start date.';
  else if (startDate < today) errors.startDate = 'Start date cannot be in the past.';

  if (!endDate) errors.endDate = 'End date is required.';
  else if (!validDate(endDate)) errors.endDate = 'Enter a valid end date.';
  else if (endDate < today) errors.endDate = 'End date cannot be in the past.';
  else if (startDate && validDate(startDate) && endDate < startDate) {
    errors.endDate = 'End date must be the same as or later than the start date.';
  }
  return errors;
}

export function validateTripForm(form) {
  const errors = {};
  const destination = String(form.destination ?? '').trim();
  if (!destination) errors.destination = 'Destination is required.';
  else if (destination.length < 2) errors.destination = 'Destination must contain at least 2 characters.';
  else if (destination.length > 150) errors.destination = 'Destination cannot exceed 150 characters.';

  const budgetText = String(form.budget ?? '').trim();
  const budget = Number(budgetText);
  if (!budgetText) errors.budget = 'Budget is required.';
  else if (!Number.isFinite(budget) || budget <= 0) errors.budget = 'Budget must be a valid number greater than zero.';

  const daysText = String(form.days ?? '').trim();
  const days = Number(daysText);
  if (!daysText) errors.days = 'Number of days is required.';
  else if (!Number.isInteger(days) || days < 1 || days > 30) errors.days = 'Travel days must be a whole number between 1 and 30.';

  Object.assign(errors, validateTripDates(form.startDate, form.endDate));
  if (!String(form.travelers ?? '').trim()) errors.travelers = 'Select a traveler category.';
  if (!String(form.travelStyle ?? '').trim()) errors.travelStyle = 'Select a travel style.';
  if (!String(form.season ?? '').trim()) errors.season = 'Select a season or climate.';
  if (!String(form.interests ?? '').trim()) errors.interests = 'Enter at least one interest.';
  if (String(form.interests ?? '').length > 1000) errors.interests = 'Interests cannot exceed 1000 characters.';
  if (String(form.specialRequirements ?? '').length > 2000) errors.specialRequirements = 'Special requirements cannot exceed 2000 characters.';
  if (!['USD', 'INR'].includes(form.currency)) errors.currency = 'Select a supported currency.';
  return errors;
}

export function validateReplanForm({ reason, newBudget, currency, weatherCondition, customWeather, crowdedLocation, newTripDays }) {
  const errors = {};
  const reasons = ['Budget Changed', 'Weather Conditions Changed', 'Crowded / Queue Mitigation', 'Trip Duration Changed'];
  if (!reasons.includes(reason)) errors.reason = 'Select a valid reason for replanning.';

  if (reason === 'Budget Changed') {
    const text = String(newBudget ?? '').trim();
    const value = Number(text);
    if (!text) errors.newBudget = 'New budget is required.';
    else if (!Number.isFinite(value) || value <= 0) errors.newBudget = 'Budget must be a valid number greater than zero.';
    if (!['USD', 'INR'].includes(currency)) errors.currency = 'Select a supported currency.';
  } else if (reason === 'Weather Conditions Changed') {
    const options = ['Heavy Rain', 'Storm / Thunderstorm', 'Snow', 'Extreme Heat', 'Cold Weather', 'Strong Winds', 'Fog / Poor Visibility', 'Other'];
    if (!options.includes(weatherCondition)) errors.weatherCondition = 'Select a valid weather condition.';
    if (weatherCondition === 'Other') {
      const value = String(customWeather ?? '').trim();
      if (!value) errors.customWeather = 'Describe the new weather condition.';
      else if (value.length > 300) errors.customWeather = 'Weather description cannot exceed 300 characters.';
    }
  } else if (reason === 'Crowded / Queue Mitigation') {
    const value = String(crowdedLocation ?? '').trim();
    if (!value) errors.crowdedLocation = 'Enter the crowded place or location.';
    else if (value.length > 300) errors.crowdedLocation = 'Location cannot exceed 300 characters.';
  } else if (reason === 'Trip Duration Changed') {
    const text = String(newTripDays ?? '').trim();
    const value = Number(text);
    if (!text) errors.newTripDays = 'New trip duration is required.';
    else if (!Number.isInteger(value) || value < 1 || value > 30) errors.newTripDays = 'Trip duration must be a whole number between 1 and 30.';
  }
  return errors;
}
