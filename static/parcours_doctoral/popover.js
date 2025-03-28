/*
 *
 * OSIS stands for Open Student Information System. It's an application
 * designed to manage the core business of higher education institutions,
 * such as universities, faculties, institutes and professional schools.
 * The core business involves the administration of students, teachers,
 * courses, programs and so on.
 *
 * Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * A copy of this license - GNU General Public License - is available
 * at the root of the source code of this program.  If not,
 * see http://www.gnu.org/licenses/.
 *
 */

function initializePopover(configuration) {
  new bootstrap.Popover(document.body, {...configuration, ...{
    selector: '.popover-buttons',
    html: true,
    placement: 'top',
    fallbackPlacements: ['auto'],
    trigger: 'focus',
  }});
}

$(function () {
  const body = $('body');

  // To prevent the popover from closing when clicking inside it (i.e. when a link is inside a popover)
  body.on('mousedown', '.popover', function(e) {
    e.preventDefault();
    return false;
  });

  // To prevent to trigger another action when we want to open a popover (i.e. when the button is inside a label)
  body.on('click', '.popover-buttons', function(e) {
    e.preventDefault();
    return false;
  });
});
