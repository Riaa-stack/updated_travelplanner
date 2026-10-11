import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Sparkles, 
  MapPin, 
  Calendar, 
  Compass, 
  Users, 
  Hotel, 
  Bus, 
  Sliders, 
  Heart, 
  Sun,
  FileText
} from 'lucide-react';
import { useTrips } from '../context/TripContext';
import DashboardLayout from '../layouts/DashboardLayout';
import Card from '../components/Card';
import Input from '../components/Input';
import Dropdown from '../components/Dropdown';
import Button from '../components/Button';
import Loader from '../components/Loader';
import Modal from '../components/Modal';
import { DESTINATION_PRESETS } from '../utils/mockData';
import { getLocalDateString, validateTripForm, validateTripDates } from '../utils/validation';

export default function PlanTripPage() {
  const { planTrip, generating, currentStep, error: tripError } = useTrips();
  const navigate = useNavigate();

  const [destination, setDestination] = useState('Tokyo & Kyoto, Japan');
  const [days, setDays] = useState('7');
  const [currency, setCurrency] = useState("USD");
  const [budget, setBudget] = useState("2800");
  const [travelStyle, setTravelStyle] = useState('Cultural & Luxury');
  const [interests, setInterests] = useState('Historical Temples, Culinary Fine Dining, Cherry Blossom Gardens, Anime & Tech');
  const [season, setSeason] = useState('Spring (Cherry Blossom)');
  const [travelers, setTravelers] = useState('Couple (2)');
  const initialStartDate = getLocalDateString();
  const initialEndDate = (() => { const d = new Date(); d.setDate(d.getDate() + 7); return getLocalDateString(d); })();
  const [startDate, setStartDate] = useState(initialStartDate);
  const [endDate, setEndDate] = useState(initialEndDate);
  const [errors, setErrors] = useState({});
  const [accommodation, setAccommodation] = useState('Boutique Luxury Hotel');
  const [transport, setTransport] = useState('Bullet Train & Private Taxi');
  const [specialReqs, setSpecialReqs] = useState('Prefer non-smoking rooms, early morning museum entries to avoid heavy crowds.');

  const [activeStepText, setActiveStepText] = useState('Analyzing Preferences');

  const getFormData = () => ({
    destination, days, budget, currency, travelStyle, interests, season, travelers,
    startDate, endDate, accommodationPreference: accommodation,
    transportPreference: transport, specialRequirements: specialReqs
  });

  const updateField = (field, value, setter) => {
    setter(value);
    const nextForm = { ...getFormData(), [field]: value };
    const nextErrors = validateTripForm(nextForm);
    setErrors((previous) => {
      const next = { ...previous };
      if (field === 'startDate' || field === 'endDate') {
        delete next.startDate;
        delete next.endDate;
        if (nextErrors.startDate) next.startDate = nextErrors.startDate;
        if (nextErrors.endDate) next.endDate = nextErrors.endDate;
      } else if (nextErrors[field]) {
        next[field] = nextErrors[field];
      } else {
        delete next[field];
      }
      return next;
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const formData = getFormData();
    const validationErrors = validateTripForm(formData);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) return;

    try {
      const newTrip = await planTrip({ ...formData, destination: destination.trim(), interests: interests.trim(), specialRequirements: specialReqs.trim() }, (stepText) => {
        setActiveStepText(stepText);
      });
      if (newTrip) navigate('/trip-result');
    } catch (err) {
      // TripContext retains the API error; keep the form populated for correction/retry.
      console.error('Trip planning failed:', err);
    }
  };

  const handleSelectPreset = (preset) => {
    setDestination(preset.name);
    setErrors((previous) => ({ ...previous, destination: undefined }));
  };

  return (
    <DashboardLayout>
      <div className="space-y-8 max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="space-y-2">
          <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-2xl bg-indigo-600 text-white text-xs font-black border-2 border-slate-900 shadow-[2px_2px_0px_#0F172A]">
            <Sparkles className="w-4 h-4 text-amber-300 animate-spin" /> Agentic Travel Concierge
          </div>
          <h1 className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            Plan Your Custom AI Trip
          </h1>
          <p className="text-xs sm:text-sm text-slate-600 font-bold">
            Configure your destination, duration, budget, and travel preferences to generate a complete travel blueprint.
          </p>
        </div>

        {/* Destination Quick Presets */}
        <div className="space-y-3">
          <p className="text-xs font-black uppercase tracking-widest text-slate-500">Popular Destinations</p>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {DESTINATION_PRESETS.map((preset, idx) => {
              const isSelected = destination.toLowerCase().includes(preset.name.split(',')[0].toLowerCase());
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectPreset(preset)}
                  className={`p-2.5 rounded-2xl border-2 text-left transition-all ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50 shadow-[4px_4px_0px_#4F46E5] -translate-y-1'
                      : 'border-slate-900 bg-white hover:bg-slate-50 shadow-[2px_2px_0px_#0F172A]'
                  }`}
                >
                  <img
                    src={preset.image}
                    alt={preset.name}
                    className="w-full h-16 object-cover rounded-xl mb-2 border border-slate-900"
                    referrerPolicy="no-referrer"
                  />
                  <p className="text-xs font-black text-slate-900 truncate">{preset.name.split(',')[0]}</p>
                  <p className="text-[10px] font-bold text-slate-500">{preset.country}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Main Planner Form */}
        <Card className="p-6 sm:p-8 shadow-[6px_6px_0px_#0F172A] border-2 border-slate-900 bg-white rounded-3xl">
          <form onSubmit={handleSubmit} className="space-y-8">
            {tripError && <p role="alert" className="text-xs font-semibold text-red-700 bg-red-50 border border-red-200 rounded-xl p-3">{tripError}</p>}
            
            {/* Form Section 1: Basic Trip Parameters */}
            <div className="space-y-5">
              <div className="inline-block px-4 py-1.5 rounded-2xl bg-indigo-100 border-2 border-indigo-600 text-indigo-950 text-xs font-black shadow-[2px_2px_0px_#4F46E5]">
                1. Basic Trip Parameters
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <Input
                  label="Destination City or Country"
                  icon={MapPin}
                  value={destination}
                  onChange={(e) => updateField('destination', e.target.value, setDestination)}
                  error={errors.destination}
                  maxLength={150}
                  placeholder="e.g., Paris, France or Tokyo, Japan"
                  required
                />

                <div className="space-y-1.5">
                  <label className="block text-xs font-bold text-slate-800">
                    Target Budget
                  </label>

                  <div className="flex overflow-hidden rounded-2xl border-2 border-slate-900 bg-[#F8FAFC] shadow-[inset_0_2px_4px_rgba(0,0,0,0.06)] focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:bg-white">

                    <select
                      value={currency}
                      onChange={(e) => setCurrency(e.target.value)}
                      className="w-24 bg-slate-200 border-r-2 border-slate-900 px-3 font-extrabold text-xs outline-none cursor-pointer"
                    >
                      <option value="USD">USD ($)</option>
                      <option value="INR">INR (₹)</option>
                    </select>

                    <input
                      type="number"
                      value={budget}
                      onChange={(e) => updateField('budget', e.target.value, setBudget)}
                      min="0.01"
                      step="any"
                      aria-invalid={Boolean(errors.budget)}
                      aria-describedby={errors.budget ? 'budget-error' : undefined}
                      placeholder="Enter budget"
                      className="flex-1 px-4 py-2.5 outline-none text-xs sm:text-sm font-bold bg-transparent text-slate-900"
                      required
                    />

                  </div>
                  {errors.currency && <p className="text-[11px] text-red-600 mt-1">{errors.currency}</p>}
                  {errors.budget && <p id="budget-error" className="text-[11px] font-medium text-red-600 mt-1">{errors.budget}</p>}
                </div>

                <Input
                  label="Number of Days"
                  icon={Calendar}
                  type="number"
                  min="1"
                  max="30"
                  value={days}
                  onChange={(e) => updateField('days', e.target.value, setDays)}
                  error={errors.days}
                  required
                />

                <Dropdown
                  label="Travelers Category"
                  icon={Users}
                  value={travelers}
                  onChange={(e) => updateField('travelers', e.target.value, setTravelers)}
                  error={errors.travelers}
                  options={[
                    'Solo Explorer',
                    'Couple (2)',
                    'Family with Kids (3-4)',
                    'Group of Friends (4+)',
                    'Business & Leisure'
                  ]}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
                <Input
                  label="Start Date"
                  type="date"
                  value={startDate}
                  min={getLocalDateString()}
                  onChange={(e) => updateField('startDate', e.target.value, setStartDate)}
                  error={errors.startDate}
                  required
                />
                <Input
                  label="End Date"
                  type="date"
                  value={endDate}
                  min={startDate && startDate >= getLocalDateString() ? startDate : getLocalDateString()}
                  onChange={(e) => updateField('endDate', e.target.value, setEndDate)}
                  error={errors.endDate}
                  required
                />
              </div>
            </div>

            {/* Form Section 2: Style & Preferences */}
            <div className="space-y-5 pt-4 border-t-2 border-slate-100">
              <div className="inline-block px-4 py-1.5 rounded-2xl bg-sky-100 border-2 border-sky-600 text-sky-950 text-xs font-black shadow-[2px_2px_0px_#0284C7]">
                2. Style & Atmosphere Preferences
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                <Dropdown
                  label="Travel Style"
                  icon={Compass}
                  value={travelStyle}
                  onChange={(e) => updateField('travelStyle', e.target.value, setTravelStyle)}
                  error={errors.travelStyle}
                  options={[
                    'Cultural & Luxury',
                    'Relaxed & Scenic',
                    'Fast-Paced Adventure',
                    'Foodie & Gastronomy',
                    'Budget Backpacker'
                  ]}
                />

                <Dropdown
                  label="Season / Climate"
                  icon={Sun}
                  value={season}
                  onChange={(e) => updateField('season', e.target.value, setSeason)}
                  error={errors.season}
                  options={[
                    'Spring (Cherry Blossom)',
                    'Summer (Warm & Sunny)',
                    'Autumn (Foliage & Mild)',
                    'Winter (Snow & Ski)'
                  ]}
                />

                <Dropdown
                  label="Accommodation Preference"
                  icon={Hotel}
                  value={accommodation}
                  onChange={(e) => setAccommodation(e.target.value)}
                  options={[
                    'Boutique Luxury Hotel',
                    '5-Star Grand Resort',
                    'Cozy Airbnb Apartment',
                    'Traditional Ryokan / Heritage Stay',
                    'Budget Hostel / Capsule'
                  ]}
                />

                <Dropdown
                  label="Transport Preference"
                  icon={Bus}
                  value={transport}
                  onChange={(e) => setTransport(e.target.value)}
                  options={[
                    'Public Transit & Trains',
                    'Bullet Train & Private Taxi',
                    'Rental Car',
                    'Walking & Eco Rides'
                  ]}
                />
              </div>

              <Input
                label="Interests & Passions"
                icon={Heart}
                value={interests}
                onChange={(e) => updateField('interests', e.target.value, setInterests)}
                error={errors.interests}
                maxLength={1000}
                placeholder="e.g., Michelin dining, Museums, Hiking, Shopping"
              />

              <div className="space-y-1.5">
                <label className="block text-xs font-bold text-slate-800">Special Requirements or Notes</label>
                <div className="relative">
                  <textarea
                    rows={3}
                    value={specialReqs}
                    onChange={(e) => updateField('specialRequirements', e.target.value, setSpecialReqs)}
                    maxLength={2000}
                    aria-invalid={Boolean(errors.specialRequirements)}
                    placeholder="e.g., Vegetarian options, wheelchair accessible paths, early morning starts..."
                    className="w-full text-xs sm:text-sm bg-[#F8FAFC] border-2 border-slate-900 rounded-2xl p-3 text-slate-900 font-medium shadow-[inset_0_2px_4px_rgba(0,0,0,0.06)] focus:bg-white focus:outline-none focus:border-blue-600 focus:ring-2 focus:ring-blue-500/20 transition-all"
                  />
                  {errors.specialRequirements && <p className="text-[11px] text-red-600 mt-1">{errors.specialRequirements}</p>}
                </div>
              </div>
            </div>

            {/* Submit Action */}
            <div className="pt-4 border-t-2 border-slate-100">
              <Button
                type="submit"
                fullWidth
                size="lg"
                icon={Sparkles}
                className="py-3.5 text-base shadow-[4px_4px_0px_#0F172A]"
                disabled={generating}
              >
                Generate Custom AI Itinerary
              </Button>
            </div>

          </form>
        </Card>

        {/* Animated Loading Modal */}
        <Modal
          isOpen={generating}
          onClose={() => {}}
          maxWidth="max-w-md"
        >
          <Loader
            text="Agentic AI Synthesis in Progress..."
            currentStep={activeStepText}
            stepIndex={currentStep}
          />
        </Modal>

      </div>
    </DashboardLayout>
  );
}
