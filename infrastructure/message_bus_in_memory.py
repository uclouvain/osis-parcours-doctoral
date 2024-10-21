# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2024 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################
from infrastructure.utils import AbstractMessageBusCommands, MessageBusInMemory

from .parcours_doctoral import handlers_in_memory as parcours_doctoral_handlers
from .parcours_doctoral.epreuve_confirmation import (
    handlers_in_memory as epreuve_confirmation_handlers,
)
from .parcours_doctoral.formation import handlers_in_memory as formation_handlers
from .parcours_doctoral.jury import handlers_in_memory as jury_handlers


class MessageBusInMemoryCommands(AbstractMessageBusCommands):
    command_handlers = {
        **parcours_doctoral_handlers.COMMAND_HANDLERS,
        **epreuve_confirmation_handlers.COMMAND_HANDLERS,
        **formation_handlers.COMMAND_HANDLERS,
        **jury_handlers.COMMAND_HANDLERS,
    }


message_bus_in_memory_instance = MessageBusInMemory(MessageBusInMemoryCommands.get_command_handlers())
